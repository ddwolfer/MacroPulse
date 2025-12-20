# 配置管理規格文件

本文檔定義專案的所有配置項、環境變數、以及配置管理方式。

---

## 1. 環境變數定義

### 1.1 .env.example 範本

```bash
# ============================================
# LLM API Keys
# ============================================
# Google Gemini API (主要使用)
GEMINI_API_KEY=your-gemini-api-key

# OpenAI API (備選)
OPENAI_API_KEY=sk-...

# LLM 提供商選擇: "gemini" 或 "openai"
LLM_PROVIDER=gemini

# LLM 模型選擇
# Gemini: "gemini-flash-latest", "gemini-pro", "gemini-pro-vision"
# OpenAI: "gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo"
LLM_MODEL=gemini-flash-latest

# ============================================
# 經濟數據 API
# ============================================
# FRED API Key (免費申請: https://fred.stlouisfed.org/docs/api/api_key.html)
FRED_API_KEY=your_fred_api_key_here

# ============================================
# 預測市場 API
# ============================================
# Polymarket API (目前不需要 API Key，但預留欄位)
POLYMARKET_API_KEY=

# ============================================
# 用戶配置
# ============================================
# 用戶持倉（JSON 格式，可選）
# 範例: [{"symbol": "BTC-USD", "quantity": 1.5}, {"symbol": "ETH-USD", "quantity": 10.0}]
USER_PORTFOLIO=

# ============================================
# 系統配置
# ============================================
# 日誌級別: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# 數據緩存目錄
DATA_CACHE_DIR=./data_cache

# 輸出目錄
OUTPUT_DIR=./outputs

# 請求超時時間（秒）
REQUEST_TIMEOUT=10.0

# API 重試次數
MAX_RETRIES=3

# API 重試初始延遲（秒）
RETRY_INITIAL_DELAY=1.0

# API 重試退避因子
RETRY_BACKOFF_FACTOR=2.0

# ============================================
# 緩存配置
# ============================================
# FRED 數據緩存 TTL（小時）
FRED_CACHE_TTL=24

# Polymarket 數據緩存 TTL（小時）
POLYMARKET_CACHE_TTL=1

# yfinance 數據緩存 TTL（分鐘）
YFINANCE_CACHE_TTL=15

# ============================================
# Agent 配置
# ============================================
# LLM 溫度設定（0.0-1.0）
LLM_TEMPERATURE=0.3

# Editor Agent 溫度（可稍高，需要創造性）
EDITOR_TEMPERATURE=0.5

# 最大 Token 數（用於限制輸入長度）
MAX_TOKENS=4000

# ============================================
# 數據過濾配置
# ============================================
# Polymarket 最小交易量門檻（USD）
POLYMARKET_MIN_VOLUME=100000

# 相關係數計算的歷史天數
CORRELATION_DAYS=7
```

---

## 2. config.py 結構

### 2.1 使用 Pydantic Settings

```python
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional, List, Dict
from pathlib import Path

class Settings(BaseSettings):
    """應用程式配置"""
    
    # LLM 配置
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    llm_provider: str = Field("gemini", env="LLM_PROVIDER")
    llm_model: str = Field("gemini-flash-latest", env="LLM_MODEL")
    llm_temperature: float = Field(0.3, env="LLM_TEMPERATURE", ge=0.0, le=1.0)
    editor_temperature: float = Field(0.5, env="EDITOR_TEMPERATURE", ge=0.0, le=1.0)
    max_tokens: int = Field(4000, env="MAX_TOKENS", gt=0)
    
    # API Keys
    fred_api_key: Optional[str] = Field(None, env="FRED_API_KEY")
    polymarket_api_key: Optional[str] = Field(None, env="POLYMARKET_API_KEY")
    
    # 用戶配置
    user_portfolio: Optional[str] = Field(None, env="USER_PORTFOLIO")
    
    # 系統配置
    log_level: str = Field("INFO", env="LOG_LEVEL")
    data_cache_dir: Path = Field(Path("./data_cache"), env="DATA_CACHE_DIR")
    output_dir: Path = Field(Path("./outputs"), env="OUTPUT_DIR")
    request_timeout: float = Field(10.0, env="REQUEST_TIMEOUT", gt=0.0)
    max_retries: int = Field(3, env="MAX_RETRIES", ge=1)
    retry_initial_delay: float = Field(1.0, env="RETRY_INITIAL_DELAY", gt=0.0)
    retry_backoff_factor: float = Field(2.0, env="RETRY_BACKOFF_FACTOR", gt=1.0)
    
    # 緩存配置
    fred_cache_ttl: int = Field(24, env="FRED_CACHE_TTL", gt=0)  # 小時
    polymarket_cache_ttl: int = Field(1, env="POLYMARKET_CACHE_TTL", gt=0)  # 小時
    yfinance_cache_ttl: int = Field(15, env="YFINANCE_CACHE_TTL", gt=0)  # 分鐘
    
    # 數據過濾配置
    polymarket_min_volume: float = Field(100000.0, env="POLYMARKET_MIN_VOLUME", ge=0.0)
    correlation_days: int = Field(7, env="CORRELATION_DAYS", ge=1, le=30)
    
    @validator("llm_provider")
    def validate_llm_provider(cls, v):
        if v not in ["gemini", "openai"]:
            raise ValueError("LLM_PROVIDER 必須是 'gemini' 或 'openai'")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            raise ValueError("LOG_LEVEL 必須是 DEBUG, INFO, WARNING, 或 ERROR")
        return v
    
    @validator("openai_api_key", "fred_api_key")
    def validate_required_keys(cls, v, values):
        """驗證必要的 API Key"""
        # 這裡可以加入更複雜的驗證邏輯
        return v
    
    def get_user_portfolio_list(self) -> List[Dict]:
        """解析用戶持倉 JSON 字串"""
        if not self.user_portfolio:
            return []
        import json
        try:
            return json.loads(self.user_portfolio)
        except json.JSONDecodeError:
            return []
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# 全域設定實例
settings = Settings()
```

---

## 3. 配置驗證

### 3.1 啟動時驗證

在 `main.py` 啟動時，應該驗證所有必要的配置：

```python
from src.utils.logger import setup_logger
from config import settings

def validate_config():
    """驗證配置完整性"""
    errors = []
    
    # 驗證 LLM API Key
    if settings.llm_provider == "gemini" and not settings.gemini_api_key:
        errors.append("缺少 GEMINI_API_KEY（當 LLM_PROVIDER=gemini 時）")
    elif settings.llm_provider == "openai" and not settings.openai_api_key:
        errors.append("缺少 OPENAI_API_KEY（當 LLM_PROVIDER=openai 時）")
    
    # 驗證 FRED API Key
    if not settings.fred_api_key:
        errors.append("缺少 FRED_API_KEY（必需）")
    
    # 驗證目錄存在
    settings.data_cache_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    
    if errors:
        logger.error("配置驗證失敗：")
        for error in errors:
            logger.error(f"  - {error}")
        raise ValueError("配置不完整，請檢查 .env 檔案")
    
    logger.info("✅ 配置驗證通過")

if __name__ == "__main__":
    logger = setup_logger()
    validate_config()
    # ... 繼續執行
```

---

## 4. 敏感資訊處理

### 4.1 .gitignore 設定

確保 `.gitignore` 包含：

```
.env
.env.local
*.key
*.pem
data_cache/
outputs/
__pycache__/
*.pyc
.pytest_cache/
```

### 4.2 日誌過濾

在日誌系統中過濾敏感資訊：

```python
import re
from typing import Any

def sanitize_log_message(message: str) -> str:
    """過濾日誌中的敏感資訊"""
    # 過濾 API Key
    message = re.sub(r'sk-[a-zA-Z0-9]{32,}', 'sk-***', message)
    message = re.sub(r'api_key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9]+', 'api_key=***', message)
    
    # 過濾用戶持倉細節（如果包含）
    # ... 其他過濾規則
    
    return message
```

---

## 5. 配置載入優先順序

1. **環境變數**（最高優先級）
2. **.env 檔案**
3. **預設值**（在 Pydantic Field 中定義）

---

## 6. 配置範例

### 6.1 開發環境

```bash
# .env.development
LOG_LEVEL=DEBUG
LLM_MODEL=gemini-flash-latest  # 快速且經濟
MAX_RETRIES=1  # 快速失敗
```

### 6.2 生產環境

```bash
# .env.production
LOG_LEVEL=INFO
LLM_MODEL=gemini-flash-latest  # 或 gemini-pro（如需更高品質）
MAX_RETRIES=5  # 更多重試
FRED_CACHE_TTL=48  # 更長的緩存時間
```

---

**文件版本**: v1.0  
**最後更新**: 2024

