"""
主編 Agent (Editor-in-Chief)

模擬投資銀行研究部門總監，負責最後的品質把關與報告撰寫。
參考文件：Spec_Agent_Editor_In_Chief.md, SPEC_Prompt_Templates.md
"""

import logging
from typing import Any, Type, Optional, List, Dict
from datetime import datetime

from pydantic import BaseModel

from src.agents.base_agent import BaseAgent
from src.schema.models import (
    FinalReport,
    FedAnalysisOutput,
    EconomicAnalysisOutput,
    PredictionAnalysisOutput,
    CorrelationAnalysisOutput
)

logger = logging.getLogger(__name__)


class EditorAgent(BaseAgent):
    """
    主編 Agent（研究部門總監）
    
    核心任務：
    1. 整合所有子 Agent 的分析報告
    2. 執行「矛盾檢索」：找出邏輯衝突
    3. 提煉核心洞察，刪除冗餘資訊
    4. 產出具備行動力的投資建議
    
    輸入數據：
    - fed_analysis: FedAnalysisOutput（貨幣政策分析）
    - economic_analysis: EconomicAnalysisOutput（經濟指標分析）
    - prediction_analysis: PredictionAnalysisOutput（預測市場分析）
    - correlation_analysis: CorrelationAnalysisOutput（資產連動分析）
    
    輸出：
    - FinalReport 模型
    """
    
    def __init__(self, temperature: float = 0.5):
        """
        初始化 Editor Agent
        
        Args:
            temperature: LLM 溫度（預設 0.5，需要一些創造性）
        """
        super().__init__(
            name="EditorAgent",
            temperature=temperature,
            max_retries=3
        )
        logger.info("Editor Agent 初始化完成")
    
    def get_system_prompt(self) -> str:
        """
        獲取 System Prompt
        
        Returns:
            str: Editor Agent 的 System Prompt
        """
        return """你是一位投資銀行（如高盛或大摩）的研究部門總監，負責最後的品質把關與報告撰寫。

你的核心任務：
1. 整合所有子 Agent 的分析報告
2. 執行「矛盾檢索」：找出邏輯衝突
3. 提煉核心洞察，刪除冗餘資訊
4. 產出具備行動力的投資建議

撰寫原則：
- tldr: 三句話總結，必須包含今日最關鍵的發現（最多 200 字）
- highlights: 從各分析中挑出 3-5 個最令人驚訝或最重要的發現
- investment_advice: 針對宏觀風險的具體投資建議（最多 1000 字）
- confidence_score: 基於所有 Agent 的 confidence 計算平均值
- conflicts: 如果發現邏輯衝突，必須在此列出

矛盾檢測規則：
- 如果經濟數據顯示過熱，但 Fed Agent 預期大幅降息 → 標註「政策預期與經濟數據背離」
- 如果預測市場情緒與傳統分析相反 → 標註「市場情緒與基本面分析存在預期差」
- 如果資產連動顯示異常相關性 → 在投資建議中強調風險
- 如果軟著陸評分與市場焦慮度矛盾 → 標註「經濟前景判斷分歧」

輸出要求：
- 必須以 JSON 格式輸出，嚴格遵循提供的 Schema
- tldr 必須精煉，最多三句話
- highlights 必須是具體的發現，不要泛泛而談
- 如果子 Agent 給出的資訊太籠統，請在 conflicts 中提出質疑
- 即使部分 Agent 分析缺失，也要基於可用數據提供有價值的報告

重要原則：
- 你是一位挑剔的研究總監，刪除冗餘資訊，只保留對投資決策有幫助的洞察
- 不要只是重複子 Agent 的結論，要提供綜合性的判斷
- 如果數據不完整，降低 confidence_score 並在報告中說明"""
    
    def format_user_prompt(self, data: Any) -> str:
        """
        格式化 User Prompt
        
        Args:
            data: 輸入數據，應包含：
                - fed_analysis: Optional[FedAnalysisOutput]
                - economic_analysis: Optional[EconomicAnalysisOutput]
                - prediction_analysis: Optional[PredictionAnalysisOutput]
                - correlation_analysis: Optional[CorrelationAnalysisOutput]
        
        Returns:
            str: 格式化後的 User Prompt
        """
        # 解構輸入數據
        fed_analysis = data.get("fed_analysis")
        economic_analysis = data.get("economic_analysis")
        prediction_analysis = data.get("prediction_analysis")
        correlation_analysis = data.get("correlation_analysis")
        
        # 統計可用報告數量
        available_count = sum(1 for x in [
            fed_analysis, economic_analysis, 
            prediction_analysis, correlation_analysis
        ] if x is not None)
        
        # 開始構建 Prompt
        prompt = f"""請整合以下專業分析報告，產出最終的投資研究報告。

**可用報告數量**: {available_count}/4

"""
        
        # === 貨幣政策分析 ===
        prompt += "【貨幣政策分析 - Fed Watcher】\n"
        if fed_analysis:
            prompt += f"""摘要: {fed_analysis.summary}
鷹/鴿指數: {fed_analysis.tone_index:.2f} (-1.0 極鴿 ~ 1.0 極鷹)
殖利率曲線狀態: {fed_analysis.yield_curve_status}
信心指數: {fed_analysis.confidence:.0%}
關鍵風險:
"""
            for risk in fed_analysis.key_risks[:3]:
                prompt += f"  - {risk}\n"
        else:
            prompt += "⚠️ 此分析暫時無法取得\n"
        
        # === 經濟指標分析 ===
        prompt += "\n【經濟指標分析 - Data Analyst】\n"
        if economic_analysis:
            prompt += f"""摘要: {economic_analysis.summary}
軟著陸評分: {economic_analysis.soft_landing_score:.1f}/10
通膨趨勢: {economic_analysis.inflation_trend}
就業狀況: {economic_analysis.employment_status}
信心指數: {economic_analysis.confidence:.0%}
"""
            # 關鍵指標
            if economic_analysis.key_indicators:
                prompt += "關鍵指標:\n"
                for key, value in list(economic_analysis.key_indicators.items())[:5]:
                    prompt += f"  - {key}: {value}\n"
        else:
            prompt += "⚠️ 此分析暫時無法取得\n"
        
        # === 預測市場分析 ===
        prompt += "\n【預測市場分析 - Prediction Specialist】\n"
        if prediction_analysis:
            # 情緒描述
            anxiety = prediction_analysis.market_anxiety_score
            sentiment_desc = "極度焦慮" if anxiety > 0.5 else \
                           "焦慮" if anxiety > 0.2 else \
                           "中性" if anxiety >= -0.2 else \
                           "樂觀" if anxiety >= -0.5 else "極度樂觀"
            
            prompt += f"""摘要: {prediction_analysis.summary}
市場情緒: {sentiment_desc} (焦慮指數: {anxiety:.2f})
信心指數: {prediction_analysis.confidence:.0%}
"""
            # 令人驚訝的市場
            if prediction_analysis.surprising_markets:
                prompt += "值得關注的市場變動:\n"
                for market in prediction_analysis.surprising_markets[:3]:
                    prompt += f"  - {market}\n"
            
            # 關鍵事件
            if prediction_analysis.key_events:
                prompt += "關鍵事件:\n"
                for event in prediction_analysis.key_events[:3]:
                    prompt += f"  - {event.get('market', 'N/A')}: "
                    prompt += f"機率 {event.get('probability', 0) * 100:.0f}%\n"
        else:
            prompt += "⚠️ 此分析暫時無法取得\n"
        
        # === 資產連動分析 ===
        prompt += "\n【資產連動分析 - Correlation Expert】\n"
        if correlation_analysis:
            prompt += f"""摘要: {correlation_analysis.summary}
信心指數: {correlation_analysis.confidence:.0%}
"""
            # 相關係數矩陣
            if correlation_analysis.correlation_matrix:
                prompt += "相關係數矩陣:\n"
                for pair, corr in list(correlation_analysis.correlation_matrix.items())[:5]:
                    prompt += f"  - {pair}: {corr:.2f}\n"
            
            # 風險預警
            if correlation_analysis.risk_warnings:
                prompt += "風險預警:\n"
                for warning in correlation_analysis.risk_warnings[:3]:
                    prompt += f"  - {warning}\n"
            
            # 持倉影響
            if correlation_analysis.portfolio_impact:
                prompt += "持倉影響分析:\n"
                for asset, impact in list(correlation_analysis.portfolio_impact.items())[:3]:
                    prompt += f"  - {asset}: {impact}\n"
        else:
            prompt += "⚠️ 此分析暫時無法取得\n"
        
        # === 分析要求 ===
        prompt += f"""

【任務】
1. 檢查上述報告中是否存在邏輯矛盾
2. 提煉最關鍵的 3-5 個洞察作為 highlights
3. 撰寫 tldr（三句話總結，最多 200 字）
4. 提供投資建議 investment_advice（最多 1000 字）
5. 計算整體信心指數 confidence_score（可用 Agent 的平均值）
6. 在 conflicts 中列出任何發現的邏輯衝突

請以 JSON 格式輸出，包含以下欄位：
- tldr: 字串，三句話總結（最多 200 字）
- highlights: 字串陣列，深度亮點列表（3-5 項）
- investment_advice: 字串，投資建議（最多 1000 字）
- confidence_score: 數字，0.0-1.0 的信心指數
- conflicts: 字串陣列，邏輯衝突列表（如無則為空陣列 []）
- agent_reports: 物件，格式為 {{"fed_agent": {{"status": "available"}}, "economic_agent": {{"status": "available"}}, "prediction_agent": {{"status": "unavailable"}}, "correlation_agent": {{"status": "available"}}}}，根據實際可用情況填寫

JSON 範例結構：
{{
  "tldr": "...",
  "highlights": ["亮點1", "亮點2", "亮點3"],
  "investment_advice": "...",
  "confidence_score": 0.75,
  "conflicts": ["衝突描述1"],
  "agent_reports": {{"fed_agent": {{"status": "available"}}, ...}}
}}
"""
        
        return prompt
    
    def get_output_model(self) -> Type[BaseModel]:
        """
        獲取輸出模型
        
        Returns:
            Type[BaseModel]: FinalReport 模型類別
        """
        return FinalReport
    
    def _calculate_average_confidence(
        self,
        fed_analysis: Optional[FedAnalysisOutput],
        economic_analysis: Optional[EconomicAnalysisOutput],
        prediction_analysis: Optional[PredictionAnalysisOutput],
        correlation_analysis: Optional[CorrelationAnalysisOutput]
    ) -> float:
        """
        計算所有可用 Agent 的平均信心指數
        
        Args:
            fed_analysis: 貨幣政策分析
            economic_analysis: 經濟指標分析
            prediction_analysis: 預測市場分析
            correlation_analysis: 資產連動分析
        
        Returns:
            float: 平均信心指數（0.0-1.0）
        """
        confidences = []
        
        if fed_analysis:
            confidences.append(fed_analysis.confidence)
        if economic_analysis:
            confidences.append(economic_analysis.confidence)
        if prediction_analysis:
            confidences.append(prediction_analysis.confidence)
        if correlation_analysis:
            confidences.append(correlation_analysis.confidence)
        
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)
    
    def _detect_conflicts(
        self,
        fed_analysis: Optional[FedAnalysisOutput],
        economic_analysis: Optional[EconomicAnalysisOutput],
        prediction_analysis: Optional[PredictionAnalysisOutput],
        correlation_analysis: Optional[CorrelationAnalysisOutput]
    ) -> List[str]:
        """
        偵測各 Agent 分析之間的邏輯衝突
        
        矛盾檢測規則：
        1. 經濟過熱 vs Fed 預期降息
        2. 預測市場情緒 vs 傳統分析
        3. 軟著陸評分 vs 市場焦慮度
        4. 資產連動異常
        
        Args:
            fed_analysis: 貨幣政策分析
            economic_analysis: 經濟指標分析
            prediction_analysis: 預測市場分析
            correlation_analysis: 資產連動分析
        
        Returns:
            List[str]: 衝突描述列表
        """
        conflicts = []
        
        # 衝突 1：Fed 鴿派（預期降息）但經濟強勁
        if fed_analysis and economic_analysis:
            # 如果 Fed Agent 偏鴿（< -0.3）但軟著陸評分高（> 7）
            if fed_analysis.tone_index < -0.3 and economic_analysis.soft_landing_score > 7:
                conflicts.append(
                    f"政策預期與經濟數據可能存在背離："
                    f"Fed 偏鴿（指數 {fed_analysis.tone_index:.2f}）但經濟表現強勁"
                    f"（軟著陸評分 {economic_analysis.soft_landing_score:.1f}/10）"
                )
            
            # 如果 Fed Agent 偏鷹（> 0.3）但經濟疲弱（< 4）
            if fed_analysis.tone_index > 0.3 and economic_analysis.soft_landing_score < 4:
                conflicts.append(
                    f"政策立場與經濟現實可能存在落差："
                    f"Fed 偏鷹（指數 {fed_analysis.tone_index:.2f}）但經濟面臨下行壓力"
                    f"（軟著陸評分僅 {economic_analysis.soft_landing_score:.1f}/10）"
                )
        
        # 衝突 2：預測市場情緒 vs 經濟分析
        if prediction_analysis and economic_analysis:
            # 市場極度焦慮（> 0.5）但軟著陸評分高（> 7）
            if prediction_analysis.market_anxiety_score > 0.5 and economic_analysis.soft_landing_score > 7:
                conflicts.append(
                    f"市場情緒與經濟基本面存在預期差："
                    f"預測市場顯示焦慮（指數 {prediction_analysis.market_anxiety_score:.2f}）"
                    f"但經濟數據樂觀（軟著陸評分 {economic_analysis.soft_landing_score:.1f}/10）"
                )
            
            # 市場極度樂觀（< -0.5）但軟著陸評分低（< 4）
            if prediction_analysis.market_anxiety_score < -0.5 and economic_analysis.soft_landing_score < 4:
                conflicts.append(
                    f"市場過度樂觀的風險："
                    f"預測市場顯示樂觀（指數 {prediction_analysis.market_anxiety_score:.2f}）"
                    f"但經濟數據堪憂（軟著陸評分僅 {economic_analysis.soft_landing_score:.1f}/10）"
                )
        
        # 衝突 3：預測市場情緒 vs Fed 政策預期
        if prediction_analysis and fed_analysis:
            # 市場焦慮但 Fed 偏鷹（可能忽視市場壓力）
            if prediction_analysis.market_anxiety_score > 0.4 and fed_analysis.tone_index > 0.2:
                conflicts.append(
                    f"市場壓力與 Fed 立場分歧："
                    f"預測市場顯示焦慮但 Fed 維持鷹派立場，可能存在政策風險"
                )
        
        # 衝突 4：殖利率曲線倒掛但經濟評分高
        if fed_analysis and economic_analysis:
            if fed_analysis.yield_curve_status == "倒掛" and economic_analysis.soft_landing_score > 6:
                conflicts.append(
                    f"殖利率曲線發出警訊：曲線倒掛通常預示衰退風險，"
                    f"但當前經濟數據仍顯示軟著陸可能性"
                    f"（評分 {economic_analysis.soft_landing_score:.1f}/10），需持續觀察"
                )
        
        # 衝突 5：資產連動異常警示
        if correlation_analysis:
            # 檢查相關係數中是否有異常
            matrix = correlation_analysis.correlation_matrix
            if matrix:
                # BTC 與風險資產相關性突然變化
                btc_qqq_corr = matrix.get("BTC-QQQ") or matrix.get("BTC_USD-QQQ")
                if btc_qqq_corr is not None:
                    if btc_qqq_corr > 0.8:
                        conflicts.append(
                            f"BTC 與納斯達克高度正相關（{btc_qqq_corr:.2f}），"
                            f"風險資產同步性增強，分散投資效果可能降低"
                        )
                    elif btc_qqq_corr < 0:
                        conflicts.append(
                            f"BTC 與納斯達克呈負相關（{btc_qqq_corr:.2f}），"
                            f"BTC 可能正在轉向避險資產屬性，值得關注"
                        )
        
        return conflicts
    
    def _prepare_agent_reports_summary(
        self,
        fed_analysis: Optional[FedAnalysisOutput],
        economic_analysis: Optional[EconomicAnalysisOutput],
        prediction_analysis: Optional[PredictionAnalysisOutput],
        correlation_analysis: Optional[CorrelationAnalysisOutput]
    ) -> Dict[str, Any]:
        """
        準備各 Agent 報告的摘要資訊
        
        Args:
            fed_analysis: 貨幣政策分析
            economic_analysis: 經濟指標分析
            prediction_analysis: 預測市場分析
            correlation_analysis: 資產連動分析
        
        Returns:
            Dict[str, Any]: Agent 報告摘要
        """
        reports = {}
        
        if fed_analysis:
            reports["fed_agent"] = {
                "status": "available",
                "tone_index": fed_analysis.tone_index,
                "yield_curve_status": fed_analysis.yield_curve_status,
                "confidence": fed_analysis.confidence
            }
        else:
            reports["fed_agent"] = {"status": "unavailable"}
        
        if economic_analysis:
            reports["economic_agent"] = {
                "status": "available",
                "soft_landing_score": economic_analysis.soft_landing_score,
                "inflation_trend": economic_analysis.inflation_trend,
                "confidence": economic_analysis.confidence
            }
        else:
            reports["economic_agent"] = {"status": "unavailable"}
        
        if prediction_analysis:
            reports["prediction_agent"] = {
                "status": "available",
                "market_anxiety_score": prediction_analysis.market_anxiety_score,
                "confidence": prediction_analysis.confidence
            }
        else:
            reports["prediction_agent"] = {"status": "unavailable"}
        
        if correlation_analysis:
            reports["correlation_agent"] = {
                "status": "available",
                "confidence": correlation_analysis.confidence
            }
        else:
            reports["correlation_agent"] = {"status": "unavailable"}
        
        return reports
    
    async def analyze(self, data: Any) -> Optional[FinalReport]:
        """
        執行報告整合分析
        
        Args:
            data: 輸入數據字典，包含：
                - fed_analysis: Optional[FedAnalysisOutput]
                - economic_analysis: Optional[EconomicAnalysisOutput]
                - prediction_analysis: Optional[PredictionAnalysisOutput]
                - correlation_analysis: Optional[CorrelationAnalysisOutput]
        
        Returns:
            Optional[FinalReport]: 最終報告，失敗則返回 None
        """
        # 解構輸入數據
        fed_analysis = data.get("fed_analysis")
        economic_analysis = data.get("economic_analysis")
        prediction_analysis = data.get("prediction_analysis")
        correlation_analysis = data.get("correlation_analysis")
        
        # 統計可用報告
        available_analyses = [
            fed_analysis, economic_analysis, 
            prediction_analysis, correlation_analysis
        ]
        available_count = sum(1 for x in available_analyses if x is not None)
        
        # 如果所有 Agent 都失敗，返回錯誤報告
        if available_count == 0:
            logger.error("Editor Agent: 所有子 Agent 分析均失敗，無法生成報告")
            return self._generate_error_report()
        
        logger.info(
            f"Editor Agent 開始整合報告（可用分析: {available_count}/4）"
        )
        
        # 預先計算衝突（供 Prompt 參考，但也讓 LLM 自行判斷）
        pre_detected_conflicts = self._detect_conflicts(
            fed_analysis, economic_analysis,
            prediction_analysis, correlation_analysis
        )
        
        if pre_detected_conflicts:
            logger.info(f"預先偵測到 {len(pre_detected_conflicts)} 個潛在衝突")
        
        # 計算預期信心指數
        expected_confidence = self._calculate_average_confidence(
            fed_analysis, economic_analysis,
            prediction_analysis, correlation_analysis
        )
        logger.debug(f"預期信心指數: {expected_confidence:.2%}")
        
        # 調用基礎 Agent 的分析邏輯（LLM 生成報告）
        result = await super().analyze(data)
        
        # 如果 LLM 分析成功，補充額外資訊
        if result:
            # 確保 agent_reports 包含狀態資訊
            if not result.agent_reports or result.agent_reports == {}:
                result.agent_reports = self._prepare_agent_reports_summary(
                    fed_analysis, economic_analysis,
                    prediction_analysis, correlation_analysis
                )
            
            # 合併預先偵測的衝突（如果 LLM 沒有發現）
            if pre_detected_conflicts and not result.conflicts:
                result.conflicts = pre_detected_conflicts
            elif pre_detected_conflicts:
                # 合併但避免重複
                existing_conflicts = set(result.conflicts)
                for conflict in pre_detected_conflicts:
                    if conflict not in existing_conflicts:
                        result.conflicts.append(conflict)
            
            # 更新時間戳
            result.timestamp = datetime.now()
            
            logger.info(
                f"✅ Editor Agent 報告生成完成："
                f"信心指數 = {result.confidence_score:.0%}, "
                f"亮點數 = {len(result.highlights)}, "
                f"衝突數 = {len(result.conflicts)}"
            )
        
        return result
    
    def _generate_error_report(self) -> FinalReport:
        """
        生成錯誤報告（當所有 Agent 都失敗時使用）
        
        Returns:
            FinalReport: 錯誤報告
        """
        return FinalReport(
            timestamp=datetime.now(),
            tldr="⚠️ 本次分析因數據採集問題無法完成。所有專業分析 Agent 均返回空結果。建議檢查 API 配置和網路連線後重試。",
            highlights=[
                "所有子 Agent 分析失敗",
                "建議檢查 FRED API 金鑰是否正確",
                "建議檢查 Gemini API 金鑰是否有效",
                "建議確認網路連線狀態"
            ],
            investment_advice="由於分析數據不完整，本次無法提供投資建議。請在系統恢復正常後重新執行分析。",
            confidence_score=0.0,
            agent_reports={
                "fed_agent": {"status": "unavailable"},
                "economic_agent": {"status": "unavailable"},
                "prediction_agent": {"status": "unavailable"},
                "correlation_agent": {"status": "unavailable"}
            },
            conflicts=["無法執行衝突偵測：缺少分析數據"]
        )
