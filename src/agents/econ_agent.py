"""
經濟指標分析 Agent (Data Analyst)

模擬總體經濟學家，擅長從硬數據中找出經濟循環的拐點。
參考文件：Spec_Agent_Data_Analyst.md, SPEC_Prompt_Templates.md
"""

import logging
from typing import Any, Type, Optional, Dict

from pydantic import BaseModel

from src.agents.base_agent import BaseAgent
from src.schema.models import EconomicAnalysisOutput, FREDSeries

logger = logging.getLogger(__name__)


class EconAgent(BaseAgent):
    """
    經濟指標分析 Agent
    
    核心任務：
    1. 評估經濟是否支持「軟著陸」預期
    2. 對比「當前值」與「市場預期值」
    3. 識別經濟數據的異常訊號
    
    輸入數據：
    - CPI 通膨數據
    - 失業率數據
    - 非農就業人數
    - PCE 物價指數
    - ISM PMI
    
    輸出：
    - EconomicAnalysisOutput 模型
    """
    
    # Fed 通膨目標
    FED_INFLATION_TARGET = 2.0
    
    # 失業率閾值
    UNEMPLOYMENT_LOW = 4.0      # 低於此值為強勁
    UNEMPLOYMENT_HIGH = 5.5     # 高於此值為疲弱
    
    # PMI 閾值
    PMI_EXPANSION = 50.0        # 高於此值為擴張
    PMI_STRONG_EXPANSION = 55.0 # 高於此值為強勁擴張
    
    def __init__(self, temperature: float = 0.3):
        """
        初始化 Economic Agent
        
        Args:
            temperature: LLM 溫度（預設 0.3，確保分析穩定）
        """
        super().__init__(
            name="EconAgent",
            temperature=temperature,
            max_retries=3
        )
        logger.info("Economic Agent 初始化完成")
    
    def get_system_prompt(self) -> str:
        """
        獲取 System Prompt
        
        Returns:
            str: Economic Agent 的 System Prompt
        """
        return """你是一位總體經濟學家，擅長從硬數據（Hard Data）中找出經濟循環的拐點。

你的核心任務：
1. 評估經濟是否支持「軟著陸」預期
2. 對比「當前值」與「市場預期值」
3. 識別經濟數據的異常訊號

分析框架：
- 通膨數據：CPI, PCE 的 YoY 和 MoM 變化
- 就業數據：NFP, 失業率, 初請失業金
- 領先指標：ISM PMI（製造業/服務業）

軟著陸評分標準（0-10）：
- 10: 完美軟著陸（通膨降至目標，就業強勁，無衰退）
- 7-9: 接近軟著陸（通膨下降，就業穩定）
- 4-6: 不確定（數據矛盾）
- 0-3: 硬著陸風險（通膨頑固，就業惡化）

輸出要求：
- 必須以 JSON 格式輸出，嚴格遵循提供的 Schema
- soft_landing_score: 0.0 到 10.0 之間的浮點數，基於數據客觀評分
- inflation_trend: 通膨趨勢，必須是以下三個值之一："上升", "下降", "穩定"
- employment_status: 就業狀況，必須是以下三個值之一："強勁", "疲弱", "穩定"
- key_indicators: 包含 CPI、失業率、非農就業等數值的字典
- summary: 200 字以內的經濟狀況專業解讀
- confidence: 0.0 到 1.0 之間的浮點數（例如 0.75 表示 75% 信心），基於數據完整性給出

重要原則：
- 指出數據中的矛盾點（如果存在）
- 如果數據不足，降低 confidence 並在 summary 中說明
- 關注數據的趨勢方向，不只是絕對數值
- 評估數據是否支持 Fed 的通膨目標（2%）"""
    
    def format_user_prompt(self, data: Any) -> str:
        """
        格式化 User Prompt
        
        Args:
            data: 輸入數據，應包含 FRED 系列數據字典：
                - CPIAUCSL: CPI 數據
                - UNRATE: 失業率
                - PAYEMS: 非農就業
                - PCEPI: PCE 物價指數
                - PMI: ISM PMI（可選）
        
        Returns:
            str: 格式化後的 User Prompt
        """
        # 解構輸入數據（支援 dict 或 FREDSeries 物件）
        fred_data = data.get("fred_data", {}) if isinstance(data, dict) else {}
        
        # 開始構建 Prompt
        prompt = "請分析以下經濟指標數據：\n\n"
        
        # === 通膨數據 ===
        prompt += "【通膨數據】\n"
        
        cpi_data = fred_data.get("CPIAUCSL")
        if cpi_data:
            latest_cpi, prev_cpi, yoy_change = self._get_cpi_analysis(cpi_data)
            if latest_cpi is not None:
                prompt += f"CPI (最新值): {latest_cpi:.2f}\n"
                if yoy_change is not None:
                    prompt += f"CPI 年增率: {yoy_change:.2f}%\n"
                    if yoy_change > self.FED_INFLATION_TARGET:
                        prompt += f"[!] 高於 Fed 目標 ({self.FED_INFLATION_TARGET}%)\n"
                    else:
                        prompt += f"[OK] 已降至 Fed 目標 ({self.FED_INFLATION_TARGET}%) 附近\n"
        else:
            prompt += "CPI: 無數據\n"
        
        pce_data = fred_data.get("PCEPI")
        if pce_data:
            latest_pce = self._get_latest_value(pce_data)
            if latest_pce is not None:
                prompt += f"PCE 物價指數 (最新值): {latest_pce:.2f}\n"
        
        # === 就業數據 ===
        prompt += "\n【就業數據】\n"
        
        unrate_data = fred_data.get("UNRATE")
        if unrate_data:
            latest_unrate = self._get_latest_value(unrate_data)
            if latest_unrate is not None:
                prompt += f"失業率: {latest_unrate:.1f}%\n"
                if latest_unrate < self.UNEMPLOYMENT_LOW:
                    prompt += "[OK] 就業市場強勁（低失業率）\n"
                elif latest_unrate > self.UNEMPLOYMENT_HIGH:
                    prompt += "[!] 就業市場疲弱（高失業率）\n"
                else:
                    prompt += "[-] 就業市場穩定\n"
        else:
            prompt += "失業率: 無數據\n"
        
        nfp_data = fred_data.get("PAYEMS")
        if nfp_data:
            latest_nfp, mom_change = self._get_nfp_analysis(nfp_data)
            if latest_nfp is not None:
                prompt += f"非農就業人數: {latest_nfp:,.0f} 千人\n"
                if mom_change is not None:
                    prompt += f"月增: {mom_change:+,.0f} 千人\n"
                    if mom_change > 200:
                        prompt += "[OK] 新增就業強勁\n"
                    elif mom_change < 0:
                        prompt += "[!] 就業流失\n"
        else:
            prompt += "非農就業: 無數據\n"
        
        # === 領先指標 ===
        prompt += "\n【領先指標】\n"
        
        pmi_data = fred_data.get("ISM_PMI")
        if pmi_data:
            latest_pmi = self._get_latest_value(pmi_data)
            if latest_pmi is not None:
                prompt += f"ISM 製造業 PMI: {latest_pmi:.1f}\n"
                if latest_pmi < self.PMI_EXPANSION:
                    prompt += "[!] PMI 低於 50，顯示製造業收縮\n"
                elif latest_pmi > self.PMI_STRONG_EXPANSION:
                    prompt += "[OK] PMI 顯示製造業強勁擴張\n"
                else:
                    prompt += "[-] PMI 顯示製造業溫和擴張\n"
        else:
            prompt += "ISM PMI: 無數據（將降低分析信心度）\n"
        
        # === 數據完整性評估 ===
        available_count = sum(1 for k in ["CPIAUCSL", "UNRATE", "PAYEMS", "PCEPI"] 
                             if fred_data.get(k) is not None)
        prompt += f"\n【數據完整性】\n"
        prompt += f"核心指標可用: {available_count}/4\n"
        if available_count < 3:
            prompt += "[!] 數據不完整，分析結果可能不夠準確\n"
        
        # === 分析要求 ===
        prompt += "\n請基於以上數據，評估經濟軟著陸的可能性，並提供專業分析。"
        prompt += "\n請特別說明通膨趨勢、就業狀況，以及整體經濟是否支持軟著陸預期。"
        prompt += "\n\n【重要】輸出格式要求："
        prompt += "\n- confidence 必須是 0.0 到 1.0 之間的小數（如 0.75），不要使用百分比或整數"
        prompt += "\n- soft_landing_score 必須是 0.0 到 10.0 之間的小數"
        
        return prompt
    
    def get_output_model(self) -> Type[BaseModel]:
        """
        獲取輸出模型
        
        Returns:
            Type[BaseModel]: EconomicAnalysisOutput 模型類別
        """
        return EconomicAnalysisOutput
    
    def _get_latest_value(self, series: Any) -> Optional[float]:
        """
        獲取系列的最新值
        
        Args:
            series: FREDSeries 物件或 dict
            
        Returns:
            Optional[float]: 最新值
        """
        if isinstance(series, FREDSeries):
            return series.get_latest_value()
        elif isinstance(series, dict):
            # 如果是 dict，嘗試轉換為 FREDSeries
            try:
                fred_series = FREDSeries(**series)
                return fred_series.get_latest_value()
            except Exception:
                return None
        return None
    
    def _get_cpi_analysis(self, cpi_data: Any) -> tuple:
        """
        分析 CPI 數據
        
        Args:
            cpi_data: CPI 系列數據
            
        Returns:
            tuple: (最新值, 上期值, 年增率)
        """
        if isinstance(cpi_data, FREDSeries):
            series = cpi_data
        elif isinstance(cpi_data, dict):
            try:
                series = FREDSeries(**cpi_data)
            except Exception:
                return (None, None, None)
        else:
            return (None, None, None)
        
        observations = [obs for obs in series.observations if obs.value is not None]
        if len(observations) < 2:
            return (None, None, None)
        
        # 按日期排序（最新在前）
        observations.sort(key=lambda x: x.date, reverse=True)
        
        latest = observations[0].value
        prev = observations[1].value if len(observations) > 1 else None
        
        # 計算年增率（假設月度數據，取 12 個月前對比）
        yoy_change = None
        if len(observations) >= 13:
            year_ago = observations[12].value
            if year_ago and year_ago > 0:
                yoy_change = ((latest - year_ago) / year_ago) * 100
        
        return (latest, prev, yoy_change)
    
    def _get_nfp_analysis(self, nfp_data: Any) -> tuple:
        """
        分析非農就業數據
        
        Args:
            nfp_data: NFP 系列數據
            
        Returns:
            tuple: (最新值, 月增量)
        """
        if isinstance(nfp_data, FREDSeries):
            series = nfp_data
        elif isinstance(nfp_data, dict):
            try:
                series = FREDSeries(**nfp_data)
            except Exception:
                return (None, None)
        else:
            return (None, None)
        
        observations = [obs for obs in series.observations if obs.value is not None]
        if len(observations) < 2:
            return (None, None)
        
        # 按日期排序（最新在前）
        observations.sort(key=lambda x: x.date, reverse=True)
        
        latest = observations[0].value
        prev = observations[1].value
        
        mom_change = latest - prev if prev else None
        
        return (latest, mom_change)
    
    async def analyze(self, data: Any) -> Optional[EconomicAnalysisOutput]:
        """
        執行經濟指標分析
        
        Args:
            data: 輸入數據字典，應包含：
                - fred_data: Dict[str, FREDSeries] (FRED 經濟數據)
        
        Returns:
            Optional[EconomicAnalysisOutput]: 分析結果，失敗則返回 None
        """
        # 驗證必要數據
        fred_data = data.get("fred_data", {}) if isinstance(data, dict) else {}
        
        if not fred_data:
            logger.warning("Economic Agent: 缺少 FRED 經濟數據，無法分析")
            return None
        
        # 統計可用數據
        available_series = [k for k, v in fred_data.items() if v is not None]
        logger.info(
            f"Economic Agent 開始分析（可用系列: {len(available_series)}）"
        )
        
        # 如果關鍵數據都缺失，則無法分析
        key_series = ["CPIAUCSL", "UNRATE", "PAYEMS"]
        key_available = [s for s in key_series if s in available_series]
        
        if len(key_available) < 2:
            logger.warning(
                f"Economic Agent: 關鍵數據不足（僅有 {key_available}），無法進行有效分析"
            )
            return None
        
        # 調用基礎 Agent 的分析邏輯
        result = await super().analyze(data)
        
        # 如果 LLM 分析成功，記錄關鍵資訊
        if result:
            logger.info(
                f"Economic Agent 分析完成："
                f"軟著陸評分 = {result.soft_landing_score:.1f}/10, "
                f"通膨趨勢 = {result.inflation_trend}, "
                f"就業狀況 = {result.employment_status}, "
                f"信心指數 = {result.confidence:.2f}"
            )
        
        return result
