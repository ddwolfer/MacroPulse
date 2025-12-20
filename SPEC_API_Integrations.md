# API 整合規格文件

本文檔定義所有外部 API 的詳細整合規格，包括端點、認證、錯誤處理等。

---

## 1. FRED API (Federal Reserve Economic Data)

### 基本資訊
- **Base URL**: `https://api.stlouisfed.org/fred/`
- **認證方式**: API Key 作為 query parameter
- **Rate Limit**: 120 requests/minute（免費版）
- **文檔**: https://fred.stlouisfed.org/docs/api/fred/

### 認證
```python
# API Key 從環境變數取得
FRED_API_KEY = os.getenv("FRED_API_KEY")

# 請求範例
url = f"https://api.stlouisfed.org/fred/series/observations"
params = {
    "series_id": "CPIAUCSL",
    "api_key": FRED_API_KEY,
    "file_type": "json"
}
```

### 必要端點

#### 1.1 獲取系列數據 (Series Observations)
- **端點**: `GET /series/observations`
- **用途**: 獲取特定經濟指標的時間序列數據

**請求參數**:
| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `series_id` | string | 是 | 系列代碼（如 CPIAUCSL） |
| `api_key` | string | 是 | FRED API Key |
| `file_type` | string | 否 | 預設 "json" |
| `limit` | integer | 否 | 返回記錄數（預設無限制） |
| `sort_order` | string | 否 | "asc" 或 "desc"（預設 "asc"） |

**響應格式**:
```json
{
  "observations": [
    {
      "realtime_start": "2024-01-01",
      "realtime_end": "2024-01-01",
      "date": "2023-12-01",
      "value": "307.671"
    }
  ]
}
```

**必要系列代碼 (Series IDs)**:
| 系列代碼 | 指標名稱 | 用途 |
|----------|----------|------|
| `CPIAUCSL` | Consumer Price Index | 通膨指標 |
| `UNRATE` | Unemployment Rate | 失業率 |
| `PAYEMS` | All Employees, Total Nonfarm | 非農就業人數 |
| `PCEPI` | Personal Consumption Expenditures: Chain-type Price Index | PCE 物價指數 |
| `PMI` | ISM Manufacturing PMI | 製造業 PMI |
| `DGS10` | 10-Year Treasury Constant Maturity Rate | 10 年期美債殖利率 |
| `DGS2` | 2-Year Treasury Constant Maturity Rate | 2 年期美債殖利率 |

### 錯誤處理
- **HTTP 400**: 無效的 series_id 或參數 → 記錄錯誤，跳過該指標
- **HTTP 403**: API Key 無效 → 拋出異常，停止執行
- **HTTP 429**: Rate Limit 超標 → 等待 60 秒後重試（最多 3 次）
- **HTTP 500**: 伺服器錯誤 → 使用緩存數據（如果存在）

---

## 2. Polymarket Gamma API

### 基本資訊
- **Base URL**: `https://gamma-api.polymarket.com`
- **認證方式**: 無需認證（公開 API）
- **Rate Limit**: 未明確說明，建議加入 1 秒請求間隔
- **文檔**: https://docs.polymarket.com/

### 必要端點

#### 2.1 獲取活躍市場列表
- **端點**: `GET /markets`
- **用途**: 獲取活躍的預測市場盤口

**請求參數**:
| 參數 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `active` | boolean | 否 | 只返回活躍市場（預設 true） |
| `closed` | boolean | 否 | 是否包含已關閉市場（預設 false） |
| `limit` | integer | 否 | 返回數量（預設 20，最大 100） |
| `category` | string | 否 | 市場類別（Macro, Politics, Crypto） |

**請求範例**:
```python
url = "https://gamma-api.polymarket.com/markets"
params = {
    "active": "true",
    "closed": "false",
    "limit": 20
}
```

**響應格式**:
```json
{
  "data": [
    {
      "id": "0x123...",
      "question": "Will the Fed cut rates in January 2024?",
      "slug": "fed-cut-rates-jan-2024",
      "outcomes": ["Yes", "No"],
      "volume": "150000.50",
      "liquidity": "200000.00",
      "endDate": "2024-01-31T00:00:00Z",
      "image": "https://...",
      "active": true,
      "new": false,
      "marketMakerAddress": "0x456...",
      "tokens": [
        {
          "outcome": "Yes",
          "price": "0.45",
          "volume": "75000.25"
        }
      ]
    }
  ]
}
```

**數據過濾邏輯**:
- 優先選擇 `volume > 100000` 的市場
- 優先選擇 `category == "Macro"` 的市場
- 計算 7 天價格變動：`price_change_7d = current_price - price_7d_ago`

### 錯誤處理
- **HTTP 429**: Rate Limit → 等待 2 秒後重試（最多 3 次）
- **HTTP 500**: 伺服器錯誤 → 返回空列表，記錄警告
- **網路超時**: 超時 10 秒 → 重試（最多 3 次）

---

## 3. yfinance (Yahoo Finance)

### 基本資訊
- **套件**: `yfinance` (Python 套件)
- **認證**: 無需認證
- **Rate Limit**: 無明確限制，但建議加入請求間隔

### 使用方式

#### 3.1 獲取美債殖利率
```python
import yfinance as yf

# 3 個月國庫券
ticker_3m = yf.Ticker("^IRX")
data_3m = ticker_3m.history(period="7d")

# 5 年期
ticker_5y = yf.Ticker("^FVX")
data_5y = ticker_5y.history(period="7d")

# 10 年期
ticker_10y = yf.Ticker("^TNX")
data_10y = ticker_10y.history(period="7d")

# 2 年期（需要特殊處理，可能使用 ^IRX 或其他）
ticker_2y = yf.Ticker("^IRX")  # 注意：需要確認正確的 ticker
```

#### 3.2 獲取資產價格
```python
# 加密貨幣
btc = yf.Ticker("BTC-USD")
eth = yf.Ticker("ETH-USD")

# 美股 ETF
spy = yf.Ticker("SPY")
qqq = yf.Ticker("QQQ")

# 美元指數
dxy = yf.Ticker("DX-Y.NYB")  # 注意：需要確認正確的 ticker

# 獲取 7 天歷史數據
history = ticker.history(period="7d")
```

**返回數據格式**:
```python
# DataFrame 格式
# Columns: Open, High, Low, Close, Volume, Dividends, Stock Splits
# Index: DatetimeIndex
```

### 錯誤處理
- **網路錯誤**: 重試 3 次，指數退避
- **無效 Ticker**: 記錄錯誤，返回空 DataFrame
- **數據缺失**: 使用最近可用數據，記錄警告

---

## 4. 通用錯誤處理策略

### 重試機制
所有 API 呼叫必須實作以下重試邏輯：

```python
import asyncio
from typing import Callable, Any

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Any:
    """
    指數退避重試機制
    
    Args:
        func: 要執行的異步函數
        max_retries: 最大重試次數
        initial_delay: 初始延遲（秒）
        backoff_factor: 退避因子
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay)
            delay *= backoff_factor
```

### 超時設定
所有 HTTP 請求必須設定超時：

```python
import httpx

async with httpx.AsyncClient(timeout=10.0) as client:
    response = await client.get(url, params=params)
```

### 緩存策略
- **緩存位置**: `data_cache/` 目錄
- **緩存格式**: JSON 檔案
- **TTL (Time To Live)**:
  - FRED 數據: 24 小時（經濟數據更新頻率低）
  - Polymarket 數據: 1 小時（市場數據變化快）
  - yfinance 數據: 15 分鐘（價格數據變化快）
- **緩存鍵命名**: `{source}_{series_id}_{date}.json`

---

## 5. API 使用優先順序

當多個數據源可用時，優先順序如下：

1. **緩存數據**（如果未過期）→ 直接使用
2. **主要 API**（FRED, Polymarket, yfinance）→ 正常請求
3. **備用數據源**（如果主要 API 失敗）→ 使用替代方案
4. **降級處理**（如果所有 API 都失敗）→ 標註數據缺失，繼續執行

---

**文件版本**: v1.0  
**最後更新**: 2024

