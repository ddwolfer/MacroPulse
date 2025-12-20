# 錯誤處理與降級策略規格文件

本文檔定義所有錯誤情況的處理方式、重試機制、以及優雅降級策略。

---

## 1. 錯誤分類

### 1.1 API 錯誤

| 錯誤類型 | HTTP 狀態碼 | 處理策略 | 降級方案 |
|----------|------------|----------|----------|
| **Rate Limit** | 429 | 指數退避重試（最多 3 次） | 使用緩存數據 |
| **認證失敗** | 401, 403 | 立即停止，記錄錯誤 | 無（必須修復） |
| **資源不存在** | 404 | 記錄警告，跳過該資源 | 標註數據缺失 |
| **伺服器錯誤** | 500, 502, 503 | 重試 3 次，指數退避 | 使用緩存數據 |
| **網路超時** | Timeout | 重試 3 次，指數退避 | 使用緩存數據 |
| **無效請求** | 400 | 記錄錯誤，跳過該請求 | 標註數據缺失 |

### 1.2 LLM 錯誤

| 錯誤類型 | 處理策略 | 降級方案 |
|----------|----------|----------|
| **API 限額超標** | 記錄錯誤，等待後重試 | 跳過該 Agent，標註缺失 |
| **JSON 解析失敗** | 嘗試修復或重新請求 | 返回空結構，記錄警告 |
| **Token 超限** | 截斷輸入數據，重新請求 | 使用摘要數據 |
| **內容過濾** | 記錄警告，返回空結構 | 標註「內容無法生成」 |

### 1.3 數據驗證錯誤

| 錯誤類型 | 處理策略 | 降級方案 |
|----------|----------|----------|
| **Pydantic 驗證失敗** | 記錄錯誤，嘗試修復 | 使用部分有效數據 |
| **數據缺失** | 記錄警告 | 使用預設值或標註缺失 |
| **數據格式異常** | 嘗試轉換或清理 | 跳過異常數據點 |

---

## 2. 重試機制實作

### 2.1 指數退避重試

```python
import asyncio
import logging
from typing import Callable, TypeVar, Optional
from functools import wraps

T = TypeVar('T')

logger = logging.getLogger(__name__)

async def retry_with_exponential_backoff(
    func: Callable[[], T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
) -> Optional[T]:
    """
    指數退避重試機制
    
    Args:
        func: 要執行的異步函數
        max_retries: 最大重試次數
        initial_delay: 初始延遲（秒）
        backoff_factor: 退避因子
        max_delay: 最大延遲（秒）
        exceptions: 要捕獲的異常類型
    
    Returns:
        函數返回值，如果所有重試都失敗則返回 None
    """
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            if attempt == max_retries - 1:
                logger.error(f"重試 {max_retries} 次後仍然失敗: {str(e)}")
                return None
            
            logger.warning(
                f"嘗試 {attempt + 1}/{max_retries} 失敗: {str(e)}. "
                f"等待 {delay:.2f} 秒後重試..."
            )
            await asyncio.sleep(delay)
            delay = min(delay * backoff_factor, max_delay)
    
    return None
```

### 2.2 HTTP 請求重試裝飾器

```python
import httpx
from typing import Optional

async def fetch_with_retry(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: float = 10.0,
    max_retries: int = 3
) -> Optional[httpx.Response]:
    """
    帶重試機制的 HTTP 請求
    
    Args:
        url: 請求 URL
        params: 查詢參數
        headers: 請求標頭
        timeout: 超時時間（秒）
        max_retries: 最大重試次數
    
    Returns:
        Response 物件，失敗則返回 None
    """
    async def _fetch():
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response
    
    # 只對特定異常重試
    retryable_exceptions = (
        httpx.HTTPStatusError,  # 5xx 錯誤
        httpx.TimeoutException,
        httpx.NetworkError
    )
    
    return await retry_with_exponential_backoff(
        _fetch,
        max_retries=max_retries,
        exceptions=retryable_exceptions
    )
```

---

## 3. 緩存策略

### 3.1 緩存讀取邏輯

```python
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import Optional, TypeVar, Type
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class CacheManager:
    """緩存管理器"""
    
    def __init__(self, cache_dir: Path, ttl_hours: int):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
    
    def get_cache_path(self, key: str) -> Path:
        """生成緩存檔案路徑"""
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"
    
    def get(self, key: str, model_class: Type[T]) -> Optional[T]:
        """
        從緩存讀取數據
        
        Returns:
            如果緩存有效則返回數據，否則返回 None
        """
        cache_path = self.get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        # 檢查是否過期
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime > self.ttl:
            logger.info(f"緩存已過期: {key}")
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return model_class(**data)
        except Exception as e:
            logger.warning(f"讀取緩存失敗 {key}: {str(e)}")
            return None
    
    def set(self, key: str, data: BaseModel):
        """寫入緩存"""
        cache_path = self.get_cache_path(key)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data.model_dump(), f, indent=2, default=str)
            logger.info(f"緩存已寫入: {key}")
        except Exception as e:
            logger.error(f"寫入緩存失敗 {key}: {str(e)}")
```

### 3.2 使用緩存的 Collector 範例

```python
from src.schema.models import FREDSeries
from config import settings

class FREDCollector:
    def __init__(self):
        self.cache = CacheManager(
            settings.data_cache_dir / "fred",
            settings.fred_cache_ttl
        )
    
    async def fetch_series(self, series_id: str) -> Optional[FREDSeries]:
        """獲取 FRED 系列數據（帶緩存）"""
        cache_key = f"fred_{series_id}"
        
        # 先嘗試從緩存讀取
        cached_data = self.cache.get(cache_key, FREDSeries)
        if cached_data:
            logger.info(f"使用緩存數據: {series_id}")
            return cached_data
        
        # 緩存未命中，從 API 獲取
        try:
            data = await self._fetch_from_api(series_id)
            if data:
                self.cache.set(cache_key, data)
            return data
        except Exception as e:
            logger.error(f"獲取 FRED 數據失敗 {series_id}: {str(e)}")
            # 即使 API 失敗，也嘗試返回過期緩存（降級）
            expired_cache = self.cache.get(cache_key, FREDSeries)
            if expired_cache:
                logger.warning(f"使用過期緩存數據: {series_id}")
            return expired_cache
```

---

## 4. Agent 錯誤處理

### 4.1 Agent 錯誤模型

```python
from src.schema.models import AgentError
from datetime import datetime

class AgentExecutionError(Exception):
    """Agent 執行錯誤"""
    def __init__(self, agent_name: str, error_type: str, error_message: str, can_continue: bool = True):
        self.agent_name = agent_name
        self.error_type = error_type
        self.error_message = error_message
        self.can_continue = can_continue
        super().__init__(f"{agent_name}: {error_message}")

def handle_agent_error(agent_name: str, error: Exception) -> AgentError:
    """處理 Agent 錯誤並返回錯誤模型"""
    error_type = type(error).__name__
    can_continue = not isinstance(error, (KeyboardInterrupt, SystemExit))
    
    logger.error(f"Agent {agent_name} 執行失敗: {error_type} - {str(error)}")
    
    return AgentError(
        agent_name=agent_name,
        error_type=error_type,
        error_message=str(error),
        can_continue=can_continue,
        timestamp=datetime.now()
    )
```

### 4.2 Agent 執行包裝器

```python
from typing import Optional, TypeVar, Callable
from functools import wraps

T = TypeVar('T')

def safe_agent_execution(agent_name: str):
    """
    Agent 執行裝飾器，確保錯誤不會中斷整個流程
    
    Usage:
        @safe_agent_execution("FedAgent")
        async def analyze(self, data):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Optional[T]:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error = handle_agent_error(agent_name, e)
                
                # 如果錯誤嚴重，記錄並返回 None
                if not error.can_continue:
                    raise
                
                # 否則返回空結構（由 Editor Agent 處理）
                logger.warning(f"{agent_name} 返回空結果，將在最終報告中標註")
                return None
        
        return wrapper
    return decorator
```

---

## 5. 降級策略

### 5.1 數據源降級

```python
class DataSourceFallback:
    """數據源降級管理器"""
    
    @staticmethod
    async def get_treasury_yield(maturity: str) -> Optional[float]:
        """
        獲取美債殖利率（帶降級）
        
        優先順序：
        1. yfinance (^TNX, ^IRX)
        2. FRED API (DGS10, DGS2)
        3. 緩存數據
        """
        # 嘗試 yfinance
        try:
            yield_data = await fetch_from_yfinance(maturity)
            if yield_data:
                return yield_data
        except Exception as e:
            logger.warning(f"yfinance 失敗，嘗試 FRED: {str(e)}")
        
        # 降級到 FRED
        try:
            yield_data = await fetch_from_fred(maturity)
            if yield_data:
                return yield_data
        except Exception as e:
            logger.warning(f"FRED 也失敗，嘗試緩存: {str(e)}")
        
        # 降級到緩存
        cached_data = cache_manager.get(f"yield_{maturity}", TreasuryYield)
        if cached_data:
            logger.warning(f"使用緩存數據: {maturity}")
            return cached_data.yield_value
        
        return None
```

### 5.2 Agent 降級

```python
async def run_all_agents_with_fallback():
    """執行所有 Agent，即使部分失敗也繼續"""
    results = {}
    errors = []
    
    agents = [
        ("FedAgent", fed_agent.analyze, fed_data),
        ("EconomicAgent", econ_agent.analyze, econ_data),
        ("PredictionAgent", prediction_agent.analyze, polymarket_data),
        ("CorrelationAgent", correlation_agent.analyze, market_data)
    ]
    
    for agent_name, analyze_func, input_data in agents:
        try:
            result = await analyze_func(input_data)
            if result:
                results[agent_name] = result
            else:
                errors.append(f"{agent_name}: 返回空結果")
        except Exception as e:
            error = handle_agent_error(agent_name, e)
            errors.append(error)
            logger.warning(f"{agent_name} 失敗，但繼續執行其他 Agent")
    
    # 即使部分 Agent 失敗，也繼續生成報告
    if results:
        final_report = await editor_agent.generate_report(results, errors)
        return final_report
    else:
        raise RuntimeError("所有 Agent 都失敗了，無法生成報告")
```

---

## 6. 錯誤報告

### 6.1 錯誤日誌格式

```python
import logging
import json
from datetime import datetime

class ErrorLogger:
    """錯誤日誌記錄器"""
    
    @staticmethod
    def log_api_error(api_name: str, url: str, status_code: int, error_msg: str):
        """記錄 API 錯誤"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "API_ERROR",
            "api": api_name,
            "url": url,
            "status_code": status_code,
            "error": error_msg
        }
        logger.error(f"API 錯誤: {json.dumps(error_data, ensure_ascii=False)}")
    
    @staticmethod
    def log_agent_error(agent_name: str, error_type: str, error_msg: str):
        """記錄 Agent 錯誤"""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "AGENT_ERROR",
            "agent": agent_name,
            "error_type": error_type,
            "error": error_msg
        }
        logger.error(f"Agent 錯誤: {json.dumps(error_data, ensure_ascii=False)}")
```

### 6.2 錯誤統計

在最終報告中包含錯誤統計：

```python
class FinalReport(BaseModel):
    # ... 其他欄位 ...
    errors: List[AgentError] = Field(default_factory=list)
    error_summary: str = Field(default="", description="錯誤摘要")
    
    def generate_error_summary(self) -> str:
        """生成錯誤摘要"""
        if not self.errors:
            return "✅ 所有 Agent 執行成功"
        
        error_counts = {}
        for error in self.errors:
            error_counts[error.agent_name] = error_counts.get(error.agent_name, 0) + 1
        
        summary = "⚠️ 部分 Agent 執行失敗：\n"
        for agent, count in error_counts.items():
            summary += f"- {agent}: {count} 個錯誤\n"
        
        return summary
```

---

## 7. 最佳實踐

### 7.1 錯誤處理原則

1. **永遠不要讓單一錯誤中斷整個流程**
2. **記錄所有錯誤，但繼續執行**
3. **使用緩存作為降級方案**
4. **在最終報告中標註數據缺失或錯誤**

### 7.2 錯誤恢復

- **可恢復錯誤**：網路超時、Rate Limit → 重試
- **部分可恢復錯誤**：數據格式異常 → 使用部分數據
- **不可恢復錯誤**：認證失敗 → 立即停止

---

**文件版本**: v1.0  
**最後更新**: 2024

