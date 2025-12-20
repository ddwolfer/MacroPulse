"""
數據模型定義

所有 Pydantic 數據模型的定義，確保數據流的一致性和類型安全。
參考文件：SPEC_Data_Models.md
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date


# =============================================================================
# 1. Collector 層數據模型
# =============================================================================

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
    category: str = Field(default="", description="市場類別（Macro, Politics, Crypto）")
    volume: float = Field(..., ge=0.0, description="總交易量（USD）")
    liquidity: float = Field(..., ge=0.0, description="流動性（USD）")
    active: bool = Field(..., description="是否活躍")
    end_date: Optional[datetime] = Field(None, description="結束日期")
    tokens: List[PolymarketToken] = Field(..., description="市場代幣列表")
    price_change_7d: Optional[float] = Field(None, description="7 天價格變動")
    
    model_config = {
        "json_schema_extra": {
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
    }


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


class TreasuryYield(BaseModel):
    """美債殖利率數據"""
    symbol: str = Field(..., description="代碼（如 ^TNX, ^IRX）")
    maturity: str = Field(..., description="到期期限（如 '10Y', '2Y'）")
    yield_value: float = Field(..., ge=0.0, description="殖利率（百分比）")
    timestamp: datetime = Field(..., description="時間戳")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "symbol": "^TNX",
                "maturity": "10Y",
                "yield_value": 4.25,
                "timestamp": "2024-01-15T10:00:00Z"
            }
        }
    }


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
    prices: List[float] = Field(..., min_length=2, description="價格列表")
    dates: List[date] = Field(..., description="日期列表")
    
    def calculate_correlation(self, other: "AssetPriceHistory") -> float:
        """
        計算與另一個資產的相關係數
        
        Args:
            other: 另一個資產的價格歷史
            
        Returns:
            float: 相關係數（-1.0 到 1.0）
        """
        import pandas as pd
        
        df1 = pd.Series(self.prices)
        df2 = pd.Series(other.prices)
        return float(df1.corr(df2))


# =============================================================================
# 2. Agent 輸出模型
# =============================================================================

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
    key_indicators: Dict[str, Any] = Field(..., description="關鍵指標數值（CPI, 失業率等）")
    summary: str = Field(..., max_length=500, description="經濟狀況總結")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心指數")


class PredictionAnalysisOutput(BaseModel):
    """預測市場分析輸出"""
    market_anxiety_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="市場焦慮度：-1.0（極度樂觀）到 1.0（極度焦慮）"
    )
    key_events: List[Dict[str, Any]] = Field(..., description="關鍵事件列表")
    surprising_markets: List[str] = Field(..., description="令人驚訝的市場變動")
    summary: str = Field(..., max_length=500, description="預測市場總結")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心指數")


class CorrelationAnalysisOutput(BaseModel):
    """資產連動分析輸出"""
    correlation_matrix: Dict[str, float] = Field(..., description="資產間相關係數矩陣")
    risk_warnings: List[str] = Field(..., description="風險預警列表")
    portfolio_impact: Optional[Dict[str, str]] = Field(
        None,
        description="對用戶持倉的影響分析（如果提供持倉）"
    )
    summary: str = Field(..., max_length=500, description="連動分析總結")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心指數")


# =============================================================================
# 3. Editor Agent 最終輸出模型
# =============================================================================

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
    agent_reports: Dict[str, Any] = Field(..., description="各 Agent 的子報告")
    conflicts: List[str] = Field(
        default_factory=list,
        description="檢測到的邏輯衝突"
    )


# =============================================================================
# 4. 通用工具模型
# =============================================================================

class UserPortfolio(BaseModel):
    """用戶持倉模型"""
    holdings: List[Dict[str, Any]] = Field(..., description="持倉列表")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "holdings": [
                    {"symbol": "BTC-USD", "quantity": 1.5},
                    {"symbol": "ETH-USD", "quantity": 10.0},
                    {"symbol": "SPY", "quantity": 100}
                ]
            }
        }
    }


class AgentError(BaseModel):
    """Agent 錯誤模型"""
    agent_name: str = Field(..., description="Agent 名稱")
    error_type: str = Field(..., description="錯誤類型")
    error_message: str = Field(..., description="錯誤訊息")
    timestamp: datetime = Field(default_factory=datetime.now)
    can_continue: bool = Field(..., description="是否可繼續執行")

