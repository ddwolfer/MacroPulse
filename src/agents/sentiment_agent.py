"""
預測市場分析 Agent (Prediction Specialist)

模擬「地下金融觀測員」與「行為金融學家」，
透過 Polymarket 的真實金流來捕捉大眾情緒與尚未公開的訊息。
參考文件：Spec_Agent_Prediction_Specialist.md, SPEC_Prompt_Templates.md
"""

import logging
from typing import Any, Type, Optional, List

from pydantic import BaseModel

from src.agents.base_agent import BaseAgent
from src.schema.models import PredictionAnalysisOutput, PolymarketMarket

logger = logging.getLogger(__name__)


class SentimentAgent(BaseAgent):
    """
    預測市場分析 Agent
    
    核心任務：
    1. 找出機率突然發生劇烈變動的盤口
    2. 分析政治事件對金融市場的潛在外部性影響
    3. 量化市場情緒（焦慮度/樂觀度）
    
    輸入數據：
    - Polymarket 市場數據列表
    
    輸出：
    - PredictionAnalysisOutput 模型
    """
    
    # 交易量門檻（USD）
    MIN_VOLUME_THRESHOLD = 100000
    
    # 價格變動閾值（7 天變動超過此值視為「劇烈」）
    SIGNIFICANT_CHANGE_THRESHOLD = 0.15  # 15%
    
    # 高交易量閾值
    HIGH_VOLUME_THRESHOLD = 500000
    
    def __init__(self, temperature: float = 0.3):
        """
        初始化 Sentiment Agent
        
        Args:
            temperature: LLM 溫度（預設 0.3，確保分析穩定）
        """
        super().__init__(
            name="SentimentAgent",
            temperature=temperature,
            max_retries=3
        )
        logger.info("Sentiment Agent 初始化完成")
    
    def get_system_prompt(self) -> str:
        """
        獲取 System Prompt
        
        Returns:
            str: Sentiment Agent 的 System Prompt
        """
        return """你是一位「地下金融觀測員」與「行為金融學家」，專門透過預測市場的真實金流來捕捉大眾情緒與尚未公開的訊息。

你的核心任務：
1. 找出機率突然發生劇烈變動的盤口
2. 分析政治事件對金融市場的潛在外部性影響
3. 量化市場情緒（焦慮度/樂觀度）

分析重點：
- 關注交易量 > $100,000 的活躍市場
- 識別 7 天內價格變動 > 15% 的市場
- 特別關注 Macro 類別的市場（與金融直接相關）
- 分析預測市場機率與傳統新聞的對比

情緒量化標準（market_anxiety_score）：
- 1.0: 極度焦慮（多數市場顯示悲觀訊號，機率大幅下降）
- 0.5: 中度焦慮
- 0.0: 中性
- -0.5: 中度樂觀
- -1.0: 極度樂觀（多數市場顯示積極訊號，機率大幅上升）

輸出要求：
- 必須以 JSON 格式輸出，嚴格遵循提供的 Schema
- market_anxiety_score: -1.0 到 1.0 之間的浮點數
- key_events: 關鍵事件列表，每個事件包含 market（市場名稱）、probability（當前機率）、change_7d（7天變動）、volume（交易量）
- surprising_markets: 令人驚訝的市場變動列表（字串）
- summary: 200 字以內的預測市場情緒總結
- confidence: 0.0 到 1.0 之間的浮點數（例如 0.75 表示 75% 信心）

重要原則：
- 預測市場是「真金白銀」的投票，比民調更具參考價值
- 關注「預期差」：市場定價與傳統分析的差異
- 如果數據不足（市場數量少），降低 confidence 並在 summary 中說明"""
    
    def format_user_prompt(self, data: Any) -> str:
        """
        格式化 User Prompt
        
        Args:
            data: 輸入數據，應包含：
                - polymarket_data: List[PolymarketMarket]
        
        Returns:
            str: 格式化後的 User Prompt
        """
        # 解構輸入數據
        markets = data.get("polymarket_data", []) if isinstance(data, dict) else []
        
        # 開始構建 Prompt
        prompt = "請分析以下 Polymarket 預測市場數據：\n\n"
        
        if not markets:
            prompt += "【警告】目前沒有可用的預測市場數據。\n"
            prompt += "請基於此情況提供分析，並將 confidence 設為較低值。\n"
            return prompt
        
        # 過濾高交易量市場
        high_volume_markets = [
            m for m in markets 
            if m.volume >= self.MIN_VOLUME_THRESHOLD
        ]
        
        # 按交易量排序
        sorted_markets = sorted(
            high_volume_markets,
            key=lambda m: m.volume,
            reverse=True
        )[:15]  # 取前 15 個
        
        # === 市場概覽 ===
        prompt += f"【市場概覽】\n"
        prompt += f"總市場數: {len(markets)}\n"
        prompt += f"高交易量市場數 (>$100K): {len(high_volume_markets)}\n\n"
        
        # === 高交易量市場詳情 ===
        prompt += "【高交易量市場（Volume > $100,000）】\n"
        
        for i, market in enumerate(sorted_markets, 1):
            # 獲取主要代幣價格（通常是 Yes）
            yes_price = None
            if market.tokens:
                for token in market.tokens:
                    if token.outcome.lower() == "yes":
                        yes_price = token.price
                        break
                if yes_price is None:
                    yes_price = market.tokens[0].price
            
            prompt += f"\n{i}. {market.question}\n"
            prompt += f"   類別: {market.category or 'N/A'}\n"
            prompt += f"   當前機率 (Yes): {yes_price * 100:.1f}%\n" if yes_price else "   當前機率: N/A\n"
            prompt += f"   24h 交易量: ${market.volume:,.0f}\n"
            prompt += f"   流動性: ${market.liquidity:,.0f}\n"
            
            # 標記高交易量
            if market.volume > self.HIGH_VOLUME_THRESHOLD:
                prompt += f"   [!] 高交易量市場\n"
            
            # 如果有 7 天價格變動
            if market.price_change_7d is not None:
                change_pct = market.price_change_7d * 100
                prompt += f"   7 天變動: {change_pct:+.1f}%\n"
                if abs(market.price_change_7d) > self.SIGNIFICANT_CHANGE_THRESHOLD:
                    prompt += f"   [!] 劇烈變動\n"
        
        # === 分析請求 ===
        prompt += "\n【分析請求】\n"
        prompt += "1. 識別機率發生劇烈變動的市場（如有）\n"
        prompt += "2. 分析這些市場變動對金融市場的潛在影響\n"
        prompt += "3. 評估整體市場情緒（焦慮/中性/樂觀）\n"
        prompt += "4. 列出最令人驚訝或值得關注的市場\n"
        
        prompt += "\n【重要】輸出格式要求：\n"
        prompt += "- market_anxiety_score 必須是 -1.0 到 1.0 之間的小數\n"
        prompt += "- confidence 必須是 0.0 到 1.0 之間的小數（如 0.75）\n"
        prompt += "- key_events 必須是包含 market, probability, change_7d, volume 的物件列表\n"
        
        return prompt
    
    def get_output_model(self) -> Type[BaseModel]:
        """
        獲取輸出模型
        
        Returns:
            Type[BaseModel]: PredictionAnalysisOutput 模型類別
        """
        return PredictionAnalysisOutput
    
    def _calculate_market_sentiment(
        self,
        markets: List[PolymarketMarket]
    ) -> float:
        """
        基於市場數據初步計算情緒指數
        
        Args:
            markets: Polymarket 市場列表
            
        Returns:
            float: 初步情緒指數 (-1.0 到 1.0)
        """
        if not markets:
            return 0.0
        
        # 統計上漲/下跌市場
        up_count = 0
        down_count = 0
        
        for market in markets:
            if market.price_change_7d:
                if market.price_change_7d > 0.05:  # 上漲 > 5%
                    up_count += 1
                elif market.price_change_7d < -0.05:  # 下跌 > 5%
                    down_count += 1
        
        total = up_count + down_count
        if total == 0:
            return 0.0
        
        # 計算情緒：下跌多 = 焦慮（正值），上漲多 = 樂觀（負值）
        sentiment = (down_count - up_count) / total
        return max(-1.0, min(1.0, sentiment))
    
    def _identify_surprising_markets(
        self,
        markets: List[PolymarketMarket]
    ) -> List[str]:
        """
        識別令人驚訝的市場變動
        
        Args:
            markets: Polymarket 市場列表
            
        Returns:
            List[str]: 令人驚訝的市場描述列表
        """
        surprising = []
        
        for market in markets:
            # 高交易量 + 劇烈變動
            if market.volume > self.HIGH_VOLUME_THRESHOLD:
                if market.price_change_7d and abs(market.price_change_7d) > self.SIGNIFICANT_CHANGE_THRESHOLD:
                    direction = "上漲" if market.price_change_7d > 0 else "下跌"
                    surprising.append(
                        f"{market.question} - 7天{direction}{abs(market.price_change_7d)*100:.1f}%，"
                        f"交易量${market.volume:,.0f}"
                    )
        
        return surprising[:5]  # 最多返回 5 個
    
    async def analyze(self, data: Any) -> Optional[PredictionAnalysisOutput]:
        """
        執行預測市場分析
        
        Args:
            data: 輸入數據字典，應包含：
                - polymarket_data: List[PolymarketMarket]
        
        Returns:
            Optional[PredictionAnalysisOutput]: 分析結果，失敗則返回 None
        """
        # 驗證數據
        markets = data.get("polymarket_data", []) if isinstance(data, dict) else []
        
        if not markets:
            logger.warning("Sentiment Agent: 缺少 Polymarket 數據，將使用空數據分析")
        
        # 統計市場數據
        high_volume_count = sum(
            1 for m in markets 
            if m.volume >= self.MIN_VOLUME_THRESHOLD
        )
        
        logger.info(
            f"Sentiment Agent 開始分析（市場數: {len(markets)}，"
            f"高交易量: {high_volume_count}）"
        )
        
        # 調用基礎 Agent 的分析邏輯
        result = await super().analyze(data)
        
        # 如果 LLM 分析成功，記錄關鍵資訊
        if result:
            logger.info(
                f"Sentiment Agent 分析完成："
                f"焦慮指數 = {result.market_anxiety_score:.2f}, "
                f"關鍵事件數 = {len(result.key_events)}, "
                f"信心指數 = {result.confidence:.2f}"
            )
        
        return result
