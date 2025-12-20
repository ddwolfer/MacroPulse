# 數據模型規格文件

本文檔定義所有 Pydantic 數據模型的完整結構，確保數據流的一致性和類型安全。

---

## 1. Collector 層數據模型

### 1.1 Polymarket 市場數據

**檔案位置**: `src/schema/models.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PolymarketToken(BaseModel):
    """Polymarket 市場代幣（選項）"""
    outcome: str = Field(..., description="選項名稱（如 'Yes', 'No'）")
    price: float = Field(..., ge=0.0, le=1.0, description="當前價格（機率）")
    volume: float = Field(..., ge=0.0, description="24 小時交易量（USD）")

class PolymarketMarket(BaseModel):
    """Polymarket 市場數據"""
    id: str = Field(..., description="市場 ID")
    question: str = Field(..., description="市場問題")
    slug: str = Field(..., description="市場 slug")
    category: str = Field(..., description="市場類別（Macro, Politics, Crypto）")
    volume: float = Field(..., ge=0.0, description="總交易量（USD）")
    liquidity: float = Field(..., ge=0.0, description="流動性（USD）")
    active: bool = Field(..., description="是否活躍")
    end_date: Optional[datetime] = Field(None, description="結束日期")
    tokens: List[PolymarketToken] = Field(..., description="市場代幣列表")
    price_change_7d: Optional[float] = Field(None, description="7 天價格變動")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "0x123...",
                "question": "Will the Fed cut rates in January 2024?",
                "slug": "fed-cut-rates-jan-2024",
                "category": "Macro",
                "volume": 150000.50,
                "liquidity": 200000.00,
                "active": True,
                "tokens": [
                    {"outcome": "Yes", "price": 0.45, "volume": 75000.25},
                    {"outcome": "No", "price": 0.55, "volume": 75000.25}
                ]
            }
        }
```

### 1.2 FRED 經濟數據

```python
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class FREDObservation(BaseModel):
    """FRED 單一觀測值"""
    date: date = Field(..., description="觀測日期")
    value: Optional[float] = Field(None, description="數值（可能為 None，表示缺失）")
    realtime_start: date = Field(..., description="數據開始日期")
    realtime_end: date = Field(..., description="數據結束日期")

class FREDSeries(BaseModel):
    """FRED 時間序列數據"""
    series_id: str = Field(..., description="系列代碼（如 CPIAUCSL）")
    title: str = Field(..., description="系列標題")
    observations: List[FREDObservation] = Field(..., description="觀測值列表")
    units: str = Field(default="", description="單位")
    frequency: str = Field(default="", description="頻率（Monthly, Weekly 等）")
    last_updated: Optional[datetime] = Field(None, description="最後更新時間")
    
    def get_latest_value(self) -> Optional[float]:
        """獲取最新的非空數值"""
        for obs in reversed(self.observations):
            if obs.value is not None:
                return obs.value
        return None
```

### 1.3 美債殖利率數據

```python
class TreasuryYield(BaseModel):
    """美債殖利率數據"""
    symbol: str = Field(..., description="代碼（如 ^TNX, ^IRX）")
    maturity: str = Field(..., description="到期期限（如 '10Y', '2Y'）")
    yield_value: float = Field(..., ge=0.0, description="殖利率（百分比）")
    timestamp: datetime = Field(..., description="時間戳")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "^TNX",
                "maturity": "10Y",
                "yield_value": 4.25,
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }
```

### 1.4 資產價格數據

```python
class AssetPrice(BaseModel):
    """資產價格數據"""
    symbol: str = Field(..., description="資產代碼（如 BTC-USD, SPY）")
    price: float = Field(..., gt=0.0, description="當前價格")
    change_24h: float = Field(..., description="24 小時變動（百分比）")
    volume: float = Field(..., ge=0.0, description="24 小時交易量")
    timestamp: datetime = Field(..., description="時間戳")
    
class AssetPriceHistory(BaseModel):
    """資產價格歷史數據（用於計算相關係數）"""
    symbol: str = Field(..., description="資產代碼")
    prices: List[float] = Field(..., min_items=2, description="價格列表")
    dates: List[date] = Field(..., description="日期列表")
    
    def calculate_correlation(self, other: "AssetPriceHistory") -> float:
        """計算與另一個資產的相關係數"""
        import pandas as pd
        import numpy as np
        
        df1 = pd.Series(self.prices)
        df2 = pd.Series(other.prices)
        return float(df1.corr(df2))
```

---

## 2. Agent 輸出模型

### 2.1 Fed Agent 輸出

```python
class FedAnalysisOutput(BaseModel):
    """貨幣政策分析輸出"""
    tone_index: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="鷹/鴿指數：-1.0（極鴿）到 1.0（極鷹）"
    )
    key_risks: List[str] = Field(..., description="關鍵風險列表")
    summary: str = Field(..., max_length=500, description="200 字以內的專業解讀")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="信心指數：0.0（不確定）到 1.0（非常確定）"
    )
    yield_curve_status: str = Field(..., description="殖利率曲線狀態（正常/倒掛）")
    next_fomc_probability: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="下次 FOMC 降息機率（如果可取得）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "tone_index": -0.3,
                "key_risks": [
                    "市場預期降息過於樂觀",
                    "通膨可能反彈"
                ],
                "summary": "當前美債 2Y 殖利率大幅下行，顯示市場正在定價 1 月份的預防性降息。然而 FedWatch 顯示機率僅為 40%，這存在潛在的波動風險...",
                "confidence": 0.75,
                "yield_curve_status": "倒掛",
                "next_fomc_probability": 0.40
            }
        }
```

### 2.2 Economic Data Analyst 輸出

```python
class EconomicAnalysisOutput(BaseModel):
    """經濟指標分析輸出"""
    soft_landing_score: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="軟著陸評分：0.0（硬著陸）到 10.0（完美軟著陸）"
    )
    inflation_trend: str = Field(..., description="通膨趨勢（上升/下降/穩定）")
    employment_status: str = Field(..., description="就業狀況（強勁/疲弱/穩定）")
    key_indicators: dict = Field(..., description="關鍵指標數值（CPI, 失業率等）")
    summary: str = Field(..., max_length=500, description="經濟狀況總結")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心指數")
    
    class Config:
        json_schema_extra = {
            "example": {
                "soft_landing_score": 7.5,
                "inflation_trend": "下降",
                "employment_status": "強勁",
                "key_indicators": {
                    "CPI_YoY": 3.2,
                    "unemployment_rate": 3.7,
                    "NFP": 200000
                },
                "summary": "當前經濟數據顯示通膨持續降溫，就業市場保持強勁，支持軟著陸預期...",
                "confidence": 0.80
            }
        }
```

### 2.3 Prediction Specialist 輸出

```python
class PredictionAnalysisOutput(BaseModel):
    """預測市場分析輸出"""
    market_anxiety_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="市場焦慮度：-1.0（極度樂觀）到 1.0（極度焦慮）"
    )
    key_events: List[dict] = Field(..., description="關鍵事件列表")
    surprising_markets: List[str] = Field(..., description="令人驚訝的市場變動")
    summary: str = Field(..., max_length=500, description="預測市場總結")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心指數")
    
    class Config:
        json_schema_extra = {
            "example": {
                "market_anxiety_score": 0.3,
                "key_events": [
                    {
                        "market": "Fed rate cut in January",
                        "probability": 0.45,
                        "change_7d": 0.15,
                        "volume": 150000
                    }
                ],
                "surprising_markets": [
                    "某法案通過機率從 30% 躍升至 70%"
                ],
                "summary": "Polymarket 數據顯示市場對 Fed 降息預期上升，但與傳統分析存在分歧...",
                "confidence": 0.70
            }
        }
```

### 2.4 Correlation Expert 輸出

```python
class CorrelationAnalysisOutput(BaseModel):
    """資產連動分析輸出"""
    correlation_matrix: dict = Field(..., description="資產間相關係數矩陣")
    risk_warnings: List[str] = Field(..., description="風險預警列表")
    portfolio_impact: Optional[dict] = Field(
        None,
        description="對用戶持倉的影響分析（如果提供持倉）"
    )
    summary: str = Field(..., max_length=500, description="連動分析總結")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心指數")
    
    class Config:
        json_schema_extra = {
            "example": {
                "correlation_matrix": {
                    "BTC-DXY": -0.85,
                    "BTC-QQQ": 0.65,
                    "SPY-QQQ": 0.95
                },
                "risk_warnings": [
                    "美元指數強勢上漲可能壓制 Crypto 反彈",
                    "BTC 與納斯達克相關性上升，風險資產屬性增強"
                ],
                "portfolio_impact": {
                    "BTC": "負面影響：美元走強",
                    "ETH": "負面影響：美元走強"
                },
                "summary": "目前 BTC 與 DXY 呈現強負相關 (-0.85)，近期美元的走強可能是壓制 Crypto 反彈的主因...",
                "confidence": 0.85
            }
        }
```

---

## 3. Editor Agent 最終輸出模型

```python
class FinalReport(BaseModel):
    """最終報告模型"""
    timestamp: datetime = Field(default_factory=datetime.now, description="報告生成時間")
    tldr: str = Field(..., max_length=200, description="三句話總結")
    highlights: List[str] = Field(..., description="深度亮點列表")
    investment_advice: str = Field(..., max_length=1000, description="投資建議")
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="整體信心指數（所有 Agent 的平均值）"
    )
    agent_reports: dict = Field(..., description="各 Agent 的子報告")
    conflicts: List[str] = Field(
        default_factory=list,
        description="檢測到的邏輯衝突"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T10:00:00Z",
                "tldr": "市場預期 Fed 降息，但數據顯示經濟仍強勁。Polymarket 顯示降息機率 45%，與傳統分析存在分歧。建議關注美元指數走勢對 Crypto 的影響。",
                "highlights": [
                    "Polymarket 降息機率與 FedWatch 存在 10% 差異",
                    "BTC 與 DXY 負相關性達到 -0.85，創近期新高"
                ],
                "investment_advice": "當前環境下，建議減持美元相關資產，關注 Fed 政策轉向時機...",
                "confidence_score": 0.75,
                "agent_reports": {
                    "fed_agent": {...},
                    "economic_agent": {...},
                    "prediction_agent": {...},
                    "correlation_agent": {...}
                },
                "conflicts": [
                    "經濟數據顯示強勁，但 Fed Agent 預期降息，可能存在邏輯背離"
                ]
            }
        }
```

---

## 4. 通用工具模型

### 4.1 用戶持倉模型（可選）

```python
class UserPortfolio(BaseModel):
    """用戶持倉模型"""
    holdings: List[dict] = Field(..., description="持倉列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "holdings": [
                    {"symbol": "BTC-USD", "quantity": 1.5},
                    {"symbol": "ETH-USD", "quantity": 10.0},
                    {"symbol": "SPY", "quantity": 100}
                ]
            }
        }
```

### 4.2 錯誤模型

```python
class AgentError(BaseModel):
    """Agent 錯誤模型"""
    agent_name: str = Field(..., description="Agent 名稱")
    error_type: str = Field(..., description="錯誤類型")
    error_message: str = Field(..., description="錯誤訊息")
    timestamp: datetime = Field(default_factory=datetime.now)
    can_continue: bool = Field(..., description="是否可繼續執行")
```

---

## 5. 數據驗證規則

### 5.1 必填欄位檢查
所有模型在創建時必須通過 Pydantic 驗證。

### 5.2 數值範圍檢查
- 機率值：必須在 [0.0, 1.0] 範圍內
- 評分：根據具體模型定義範圍
- 價格：必須 > 0

### 5.3 字串長度限制
- Summary: 最多 500 字
- TL;DR: 最多 200 字
- 投資建議: 最多 1000 字

---

**文件版本**: v1.0  
**最後更新**: 2024

