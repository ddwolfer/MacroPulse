"""
貨幣政策分析 Agent (Fed Watcher)

模擬專精於固定收益商品與聯準會行為的資深策略師。
參考文件：Spec_Agent_Fed_Watcher.md, SPEC_Prompt_Templates.md
"""

import logging
from typing import Any, Type, Optional, List

from pydantic import BaseModel

from src.agents.base_agent import BaseAgent
from src.schema.models import FedAnalysisOutput, TreasuryYield, PolymarketMarket

logger = logging.getLogger(__name__)


class FedAgent(BaseAgent):
    """
    貨幣政策分析 Agent
    
    核心任務：
    1. 分析聯準會對於「中性利率」的態度
    2. 評估市場定價是否過於樂觀或悲觀
    3. 識別殖利率曲線的異常狀況（如倒掛）
    4. 預測 Fed 政策轉向的時機和幅度
    
    輸入數據：
    - 美債殖利率（2Y, 10Y 等）
    - FedWatch 數據（可選）
    - Polymarket 相關市場（可選）
    
    輸出：
    - FedAnalysisOutput 模型
    """
    
    def __init__(self, temperature: float = 0.3):
        """
        初始化 Fed Agent
        
        Args:
            temperature: LLM 溫度（預設 0.3，確保分析穩定）
        """
        super().__init__(
            name="FedAgent",
            temperature=temperature,
            max_retries=3
        )
        logger.info("Fed Agent 初始化完成")
    
    def get_system_prompt(self) -> str:
        """
        獲取 System Prompt
        
        Returns:
            str: Fed Agent 的 System Prompt
        """
        return """你是一位專精於「固定收益商品」與「聯準會行為」的資深策略師，擁有 20 年以上的市場經驗。

你的核心任務：
1. 分析聯準會對於「中性利率」的態度
2. 評估市場定價是否過於樂觀或悲觀
3. 識別殖利率曲線的異常狀況（如倒掛）
4. 預測 Fed 政策轉向的時機和幅度

分析框架：
- 比較市場預期（FedWatch, Polymarket）與 Fed 官員實際言論
- 觀察美債殖利率曲線的變化（2Y vs 10Y）
- 評估通膨數據與 Fed 目標的一致性

輸出要求：
- 必須以 JSON 格式輸出，嚴格遵循提供的 Schema
- tone_index: -1.0（極鴿）到 1.0（極鷹），基於當前數據客觀評估
- key_risks: 列出 3-5 個關鍵風險點
- summary: 200 字以內的專業解讀，使用金融術語但保持清晰
- confidence: 基於數據完整性和市場一致性給出信心指數
- yield_curve_status: 殖利率曲線狀態（"正常", "倒掛", "陡峭"）

重要原則：
- 不要過度解讀單一指標
- 如果數據不足，降低 confidence 並在 summary 中說明
- 指出市場預期與實際數據的「預期差」
- tone_index 應該基於多個指標綜合判斷，不只看單一數據"""
    
    def format_user_prompt(self, data: Any) -> str:
        """
        格式化 User Prompt
        
        Args:
            data: 輸入數據，應包含：
                - treasury_yields: List[TreasuryYield]
                - fedwatch_data: Optional[dict]
                - polymarket_data: Optional[List[PolymarketMarket]]
        
        Returns:
            str: 格式化後的 User Prompt
        """
        # 解構輸入數據
        treasury_yields = data.get("treasury_yields", [])
        fedwatch_data = data.get("fedwatch_data")
        polymarket_data = data.get("polymarket_data", [])
        
        # 開始構建 Prompt
        prompt = "請分析以下貨幣政策相關數據：\n\n"
        
        # === 美債殖利率數據 ===
        if treasury_yields:
            prompt += "【美債殖利率數據】\n"
            for yield_data in treasury_yields:
                prompt += (
                    f"- {yield_data.maturity}: {yield_data.yield_value:.2f}% "
                    f"(時間: {yield_data.timestamp.strftime('%Y-%m-%d %H:%M')})\n"
                )
            
            # 計算殖利率曲線利差
            yield_2y = next((y for y in treasury_yields if "2Y" in y.maturity), None)
            yield_10y = next((y for y in treasury_yields if "10Y" in y.maturity), None)
            
            if yield_2y and yield_10y:
                spread = yield_10y.yield_value - yield_2y.yield_value
                prompt += f"\n殖利率曲線利差 (10Y - 2Y): {spread:.2f}%\n"
                
                if spread < 0:
                    prompt += "*** 警告：殖利率曲線倒掛中 ***\n"
                elif spread < 0.5:
                    prompt += "*** 注意：殖利率曲線接近倒掛（利差 < 0.5%）***\n"
                elif spread > 2.0:
                    prompt += "*** 注意：殖利率曲線陡峭（利差 > 2.0%）***\n"
        else:
            prompt += "【美債殖利率數據】\n未提供數據\n"
        
        # === FedWatch 數據 ===
        if fedwatch_data:
            prompt += "\n【FedWatch 數據】\n"
            cut_prob = fedwatch_data.get("cut_probability", "N/A")
            hike_prob = fedwatch_data.get("hike_probability", "N/A")
            hold_prob = fedwatch_data.get("hold_probability", "N/A")
            
            prompt += f"下次 FOMC 降息機率: {cut_prob}%\n"
            prompt += f"維持利率機率: {hold_prob}%\n"
            prompt += f"升息機率: {hike_prob}%\n"
        
        # === Polymarket 相關市場 ===
        if polymarket_data:
            # 只取前 3 個最相關的市場
            relevant_markets = polymarket_data[:3]
            if relevant_markets:
                prompt += "\n【Polymarket 相關市場】\n"
                for market in relevant_markets:
                    if market.tokens:
                        token = market.tokens[0]
                        prompt += (
                            f"- {market.question}: {token.price * 100:.1f}% "
                            f"(交易量: ${market.volume:,.0f})\n"
                        )
        
        # === 分析要求 ===
        prompt += "\n請基於以上數據，提供專業的貨幣政策分析。"
        
        return prompt
    
    def get_output_model(self) -> Type[BaseModel]:
        """
        獲取輸出模型
        
        Returns:
            Type[BaseModel]: FedAnalysisOutput 模型類別
        """
        return FedAnalysisOutput
    
    def _calculate_yield_curve_status(
        self,
        treasury_yields: List[TreasuryYield]
    ) -> str:
        """
        計算殖利率曲線狀態
        
        Args:
            treasury_yields: 美債殖利率列表
        
        Returns:
            str: "正常", "倒掛", 或 "陡峭"
        """
        yield_2y = next((y for y in treasury_yields if "2Y" in y.maturity), None)
        yield_10y = next((y for y in treasury_yields if "10Y" in y.maturity), None)
        
        if not yield_2y or not yield_10y:
            return "正常"  # 數據不足，預設正常
        
        spread = yield_10y.yield_value - yield_2y.yield_value
        
        if spread < 0:
            return "倒掛"
        elif spread > 2.0:
            return "陡峭"
        else:
            return "正常"
    
    async def analyze(self, data: Any) -> Optional[FedAnalysisOutput]:
        """
        執行貨幣政策分析
        
        Args:
            data: 輸入數據字典，包含：
                - treasury_yields: List[TreasuryYield] (必需)
                - fedwatch_data: Optional[dict]
                - polymarket_data: Optional[List[PolymarketMarket]]
        
        Returns:
            Optional[FedAnalysisOutput]: 分析結果，失敗則返回 None
        """
        # 驗證必要數據
        treasury_yields = data.get("treasury_yields", [])
        if not treasury_yields:
            logger.warning("Fed Agent: 缺少美債殖利率數據，無法分析")
            return None
        
        logger.info(
            f"Fed Agent 開始分析（殖利率數據點: {len(treasury_yields)}）"
        )
        
        # 調用基礎 Agent 的分析邏輯
        result = await super().analyze(data)
        
        # 如果 LLM 分析成功，記錄關鍵資訊
        if result:
            logger.info(
                f"Fed Agent 分析完成："
                f"鷹/鴿指數 = {result.tone_index:.2f}, "
                f"曲線狀態 = {result.yield_curve_status}, "
                f"信心指數 = {result.confidence:.2f}"
            )
        
        return result

