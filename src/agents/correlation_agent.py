"""
資產連動分析 Agent (Correlation Expert)

模擬量化交易員或跨資產經理人，
負責把宏觀數據翻譯成對美股與加密貨幣的具體影響。
參考文件：Spec_Agent_Correlation_Expert.md, SPEC_Prompt_Templates.md
"""

import logging
from typing import Any, Type, Optional, Dict, List

from pydantic import BaseModel

from src.agents.base_agent import BaseAgent
from src.schema.models import (
    CorrelationAnalysisOutput, 
    AssetPriceHistory,
    UserPortfolio
)

logger = logging.getLogger(__name__)


class CorrelationAgent(BaseAgent):
    """
    資產連動分析 Agent
    
    核心任務：
    1. 分析資產間的相關係數變化
    2. 判斷 BTC 的屬性（避險資產 vs 風險資產）
    3. 評估美元指數 (DXY) 對持有標的的影響
    4. 如果提供用戶持倉，分析對持倉的具體影響
    
    輸入數據：
    - 資產價格歷史 (BTC, ETH, SPY, QQQ, DXY)
    - 用戶持倉（可選）
    
    輸出：
    - CorrelationAnalysisOutput 模型
    """
    
    # 核心資產列表
    CORE_ASSETS = ["BTC-USD", "ETH-USD", "SPY", "QQQ", "DX-Y.NYB"]
    
    # 相關係數閾值
    STRONG_CORRELATION = 0.7
    MODERATE_CORRELATION = 0.4
    
    def __init__(self, temperature: float = 0.3):
        """
        初始化 Correlation Agent
        
        Args:
            temperature: LLM 溫度（預設 0.3，確保分析穩定）
        """
        super().__init__(
            name="CorrelationAgent",
            temperature=temperature,
            max_retries=3
        )
        logger.info("Correlation Agent 初始化完成")
    
    def get_system_prompt(self) -> str:
        """
        獲取 System Prompt
        
        Returns:
            str: Correlation Agent 的 System Prompt
        """
        return """你是一位量化交易員或跨資產經理人，負責把宏觀數據翻譯成對美股 (SPX/NDX) 與加密貨幣 (BTC/ETH) 的具體影響。

你的核心任務：
1. 分析資產間的相關係數變化
2. 判斷 BTC 的屬性（避險資產 vs 風險資產）
3. 評估美元指數 (DXY) 對持有標的的影響
4. 如果提供用戶持倉，分析對持倉的具體風險

分析框架：
- 計算資產間的 7 天滾動相關係數
- 識別相關係數的異常變化（例如：BTC 從與 DXY 負相關轉為正相關）
- 評估用戶持倉的曝險程度

相關係數解讀：
- > 0.7: 強正相關（同向波動）
- 0.4 ~ 0.7: 中度正相關
- -0.4 ~ 0.4: 弱相關（獨立走勢）
- -0.7 ~ -0.4: 中度負相關
- < -0.7: 強負相關（反向波動）

輸出要求：
- 必須以 JSON 格式輸出，嚴格遵循提供的 Schema
- correlation_matrix: 資產配對的相關係數字典（如 {"BTC-DXY": -0.65, "BTC-QQQ": 0.72}）
- risk_warnings: 風險預警列表（字串陣列）
- portfolio_impact: 如果提供持倉，分析對每個持倉的影響（字典格式）
- summary: 200 字以內的連動分析總結
- confidence: 0.0 到 1.0 之間的浮點數（例如 0.75 表示 75% 信心）

重要原則：
- 回答核心問題：「當前環境下，BTC 是跟著黃金走（避險），還是跟著納斯達克走（風險資產）？」
- 評估：「如果美元指數 (DXY) 強勢上漲，對持有標的的負面影響有多大？」
- 如果數據不足，降低 confidence 並在 summary 中說明"""
    
    def format_user_prompt(self, data: Any) -> str:
        """
        格式化 User Prompt
        
        Args:
            data: 輸入數據，應包含：
                - asset_prices: Dict[str, AssetPriceHistory]
                - user_portfolio: Optional[UserPortfolio]
                - correlation_matrix: Optional[Dict[str, float]]（預計算的相關係數）
        
        Returns:
            str: 格式化後的 User Prompt
        """
        # 解構輸入數據
        asset_prices = data.get("asset_prices", {}) if isinstance(data, dict) else {}
        user_portfolio = data.get("user_portfolio")
        pre_calculated_corr = data.get("correlation_matrix", {})
        
        # 開始構建 Prompt
        prompt = "請分析以下資產價格數據（7 天歷史）：\n\n"
        
        if not asset_prices:
            prompt += "【警告】目前沒有可用的資產價格數據。\n"
            prompt += "請基於此情況提供分析，並將 confidence 設為較低值。\n"
            return prompt
        
        # === 資產列表 ===
        prompt += "【資產價格數據】\n"
        for symbol, history in asset_prices.items():
            if isinstance(history, AssetPriceHistory):
                prices = history.prices
                if len(prices) >= 2:
                    latest = prices[-1]
                    prev = prices[0]
                    change = ((latest - prev) / prev) * 100 if prev != 0 else 0
                    prompt += f"- {symbol}: {len(prices)} 個數據點\n"
                    prompt += f"  最新價格: ${latest:,.2f}\n"
                    prompt += f"  7 天變動: {change:+.2f}%\n"
            elif isinstance(history, dict):
                prices = history.get("prices", [])
                if len(prices) >= 2:
                    latest = prices[-1]
                    prev = prices[0]
                    change = ((latest - prev) / prev) * 100 if prev != 0 else 0
                    prompt += f"- {symbol}: {len(prices)} 個數據點\n"
                    prompt += f"  最新價格: ${latest:,.2f}\n"
                    prompt += f"  7 天變動: {change:+.2f}%\n"
        
        # === 相關係數矩陣 ===
        prompt += "\n【相關係數矩陣】\n"
        
        if pre_calculated_corr:
            for pair, corr in pre_calculated_corr.items():
                strength = self._get_correlation_strength(corr)
                prompt += f"- {pair}: {corr:.2f} ({strength})\n"
        else:
            # 嘗試計算相關係數
            corr_matrix = self._calculate_correlation_matrix(asset_prices)
            if corr_matrix:
                for pair, corr in corr_matrix.items():
                    strength = self._get_correlation_strength(corr)
                    prompt += f"- {pair}: {corr:.2f} ({strength})\n"
            else:
                prompt += "（無法計算，請基於價格趨勢進行定性分析）\n"
        
        # === 用戶持倉 ===
        if user_portfolio:
            prompt += "\n【用戶持倉】\n"
            if isinstance(user_portfolio, UserPortfolio):
                for holding in user_portfolio.holdings:
                    symbol = holding.get("symbol", "Unknown")
                    quantity = holding.get("quantity", 0)
                    prompt += f"- {symbol}: {quantity} 單位\n"
            elif isinstance(user_portfolio, dict):
                holdings = user_portfolio.get("holdings", [])
                for holding in holdings:
                    symbol = holding.get("symbol", "Unknown")
                    quantity = holding.get("quantity", 0)
                    prompt += f"- {symbol}: {quantity} 單位\n"
            prompt += "\n請分析這些持倉在當前市場環境下的風險。\n"
        
        # === 分析請求 ===
        prompt += "\n【分析請求】\n"
        prompt += "請回答以下問題：\n"
        prompt += "1. 當前環境下，BTC 是跟著黃金走（避險），還是跟著納斯達克走（風險資產）？\n"
        prompt += "2. 如果美元指數 (DXY) 強勢上漲，對持有標的的負面影響有多大？\n"
        prompt += "3. 哪些資產間的相關係數發生了異常變化？\n"
        
        if user_portfolio:
            prompt += "4. 針對用戶持倉，有哪些風險需要注意？\n"
        
        prompt += "\n【重要】輸出格式要求：\n"
        prompt += "- confidence 必須是 0.0 到 1.0 之間的小數（如 0.75）\n"
        prompt += "- correlation_matrix 必須是字典格式（如 {\"BTC-DXY\": -0.65}）\n"
        prompt += "- risk_warnings 必須是字串陣列\n"
        
        return prompt
    
    def get_output_model(self) -> Type[BaseModel]:
        """
        獲取輸出模型
        
        Returns:
            Type[BaseModel]: CorrelationAnalysisOutput 模型類別
        """
        return CorrelationAnalysisOutput
    
    def _get_correlation_strength(self, corr: float) -> str:
        """
        獲取相關係數強度描述
        
        Args:
            corr: 相關係數
            
        Returns:
            str: 強度描述
        """
        abs_corr = abs(corr)
        if abs_corr >= self.STRONG_CORRELATION:
            return "強" + ("正" if corr > 0 else "負") + "相關"
        elif abs_corr >= self.MODERATE_CORRELATION:
            return "中度" + ("正" if corr > 0 else "負") + "相關"
        else:
            return "弱相關"
    
    def _calculate_correlation_matrix(
        self,
        asset_prices: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        計算資產間的相關係數矩陣
        
        Args:
            asset_prices: 資產價格歷史
            
        Returns:
            Dict[str, float]: 相關係數字典（如 {"BTC-DXY": -0.65}）
        """
        try:
            import pandas as pd
            
            # 轉換為價格 Series
            price_series = {}
            for symbol, history in asset_prices.items():
                if isinstance(history, AssetPriceHistory):
                    price_series[symbol] = pd.Series(history.prices)
                elif isinstance(history, dict):
                    prices = history.get("prices", [])
                    if prices:
                        price_series[symbol] = pd.Series(prices)
            
            if len(price_series) < 2:
                return {}
            
            # 創建 DataFrame
            df = pd.DataFrame(price_series)
            
            # 計算相關係數矩陣
            corr_matrix = df.corr()
            
            # 轉換為字典格式（只保留非對角線元素）
            result = {}
            symbols = list(corr_matrix.columns)
            for i, sym1 in enumerate(symbols):
                for j, sym2 in enumerate(symbols):
                    if i < j:  # 避免重複
                        pair_key = f"{sym1.replace('-USD', '').replace('-Y.NYB', '')}-{sym2.replace('-USD', '').replace('-Y.NYB', '')}"
                        result[pair_key] = float(corr_matrix.loc[sym1, sym2])
            
            return result
            
        except Exception as e:
            logger.warning(f"計算相關係數失敗: {str(e)}")
            return {}
    
    def _identify_risk_warnings(
        self,
        asset_prices: Dict[str, Any],
        correlation_matrix: Dict[str, float]
    ) -> List[str]:
        """
        識別風險預警
        
        Args:
            asset_prices: 資產價格歷史
            correlation_matrix: 相關係數矩陣
            
        Returns:
            List[str]: 風險預警列表
        """
        warnings = []
        
        # 檢查 DXY 強勢
        dxy_history = asset_prices.get("DX-Y.NYB")
        if dxy_history:
            prices = dxy_history.prices if isinstance(dxy_history, AssetPriceHistory) else dxy_history.get("prices", [])
            if len(prices) >= 2:
                change = ((prices[-1] - prices[0]) / prices[0]) * 100 if prices[0] != 0 else 0
                if change > 1:
                    warnings.append(f"美元指數 7 天上漲 {change:.2f}%，可能壓制風險資產")
        
        # 檢查 BTC 與納斯達克高度正相關
        btc_qqq_corr = correlation_matrix.get("BTC-QQQ", 0)
        if btc_qqq_corr > 0.7:
            warnings.append(f"BTC 與納斯達克高度正相關 ({btc_qqq_corr:.2f})，風險資產屬性增強")
        
        # 檢查 BTC 與 DXY 負相關
        btc_dxy_corr = correlation_matrix.get("BTC-DX", 0)
        if btc_dxy_corr < -0.5:
            warnings.append(f"BTC 與美元指數負相關 ({btc_dxy_corr:.2f})，美元走強可能壓制 BTC")
        
        return warnings
    
    async def analyze(self, data: Any) -> Optional[CorrelationAnalysisOutput]:
        """
        執行資產連動分析
        
        Args:
            data: 輸入數據字典，應包含：
                - asset_prices: Dict[str, AssetPriceHistory]
                - user_portfolio: Optional[UserPortfolio]
        
        Returns:
            Optional[CorrelationAnalysisOutput]: 分析結果，失敗則返回 None
        """
        # 驗證數據
        asset_prices = data.get("asset_prices", {}) if isinstance(data, dict) else {}
        user_portfolio = data.get("user_portfolio")
        
        if not asset_prices:
            logger.warning("Correlation Agent: 缺少資產價格數據，將使用空數據分析")
        
        # 預計算相關係數矩陣
        corr_matrix = self._calculate_correlation_matrix(asset_prices)
        if corr_matrix:
            data["correlation_matrix"] = corr_matrix
        
        logger.info(
            f"Correlation Agent 開始分析（資產數: {len(asset_prices)}，"
            f"相關係數對數: {len(corr_matrix)}，"
            f"有用戶持倉: {user_portfolio is not None}）"
        )
        
        # 調用基礎 Agent 的分析邏輯
        result = await super().analyze(data)
        
        # 如果 LLM 分析成功，記錄關鍵資訊
        if result:
            logger.info(
                f"Correlation Agent 分析完成："
                f"風險預警數 = {len(result.risk_warnings)}, "
                f"信心指數 = {result.confidence:.2f}"
            )
        
        return result
