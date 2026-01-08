"""
測試 Economic Agent 功能

驗證經濟指標分析 Agent 的 Prompt 生成、數據處理和 LLM 調用。
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, date

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings, validate_config
from src.agents.econ_agent import EconAgent
from src.schema.models import FREDSeries, FREDObservation
from src.utils.logger import setup_logger

# 設定日誌
setup_logger("MacroPulse", settings.log_level)
logger = logging.getLogger(__name__)


# ============================================
# 測試數據準備
# ============================================

def create_mock_fred_data_healthy() -> dict:
    """創建模擬的健康經濟數據（支持軟著陸）"""
    today = date.today()
    
    # CPI 數據 - 模擬通膨下降
    cpi_observations = []
    base_cpi = 310.0
    for i in range(13):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        obs_date = date(year, month, 1)
        # 模擬 CPI 增速放緩（年增率約 2.5%）
        value = base_cpi - i * 0.2
        cpi_observations.append(FREDObservation(
            date=obs_date,
            value=value,
            realtime_start=obs_date,
            realtime_end=obs_date
        ))
    
    cpi_series = FREDSeries(
        series_id="CPIAUCSL",
        title="Consumer Price Index",
        observations=cpi_observations,
        units="Index 1982-1984=100",
        frequency="Monthly",
        last_updated=datetime.now()
    )
    
    # 失業率數據 - 低失業率
    unrate_observations = []
    for i in range(6):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        obs_date = date(year, month, 1)
        value = 3.7 + (i % 2) * 0.1  # 3.7-3.8%
        unrate_observations.append(FREDObservation(
            date=obs_date,
            value=value,
            realtime_start=obs_date,
            realtime_end=obs_date
        ))
    
    unrate_series = FREDSeries(
        series_id="UNRATE",
        title="Unemployment Rate",
        observations=unrate_observations,
        units="Percent",
        frequency="Monthly",
        last_updated=datetime.now()
    )
    
    # 非農就業數據 - 穩健增長
    payems_observations = []
    base_nfp = 157500  # 千人
    for i in range(3):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        obs_date = date(year, month, 1)
        value = base_nfp - i * 180  # 每月增加約 180K
        payems_observations.append(FREDObservation(
            date=obs_date,
            value=value,
            realtime_start=obs_date,
            realtime_end=obs_date
        ))
    
    payems_series = FREDSeries(
        series_id="PAYEMS",
        title="Non-Farm Payroll",
        observations=payems_observations,
        units="Thousands of Persons",
        frequency="Monthly",
        last_updated=datetime.now()
    )
    
    # PCE 數據
    pcepi_observations = [
        FREDObservation(
            date=today,
            value=118.5,
            realtime_start=today,
            realtime_end=today
        )
    ]
    
    pcepi_series = FREDSeries(
        series_id="PCEPI",
        title="PCE Price Index",
        observations=pcepi_observations,
        units="Index 2012=100",
        frequency="Monthly",
        last_updated=datetime.now()
    )
    
    return {
        "CPIAUCSL": cpi_series,
        "UNRATE": unrate_series,
        "PAYEMS": payems_series,
        "PCEPI": pcepi_series
    }


def create_mock_fred_data_concerning() -> dict:
    """創建模擬的令人擔憂經濟數據（硬著陸風險）"""
    today = date.today()
    
    # CPI 數據 - 模擬通膨頑固
    cpi_observations = []
    base_cpi = 310.0
    for i in range(13):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        obs_date = date(year, month, 1)
        # 模擬 CPI 持續上升（年增率約 5%）
        value = base_cpi - i * 0.4
        cpi_observations.append(FREDObservation(
            date=obs_date,
            value=value,
            realtime_start=obs_date,
            realtime_end=obs_date
        ))
    
    cpi_series = FREDSeries(
        series_id="CPIAUCSL",
        title="Consumer Price Index",
        observations=cpi_observations,
        units="Index 1982-1984=100",
        frequency="Monthly",
        last_updated=datetime.now()
    )
    
    # 失業率數據 - 上升中
    unrate_observations = []
    for i in range(6):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        obs_date = date(year, month, 1)
        value = 5.2 - i * 0.2  # 從 4.2% 升到 5.2%
        unrate_observations.append(FREDObservation(
            date=obs_date,
            value=value,
            realtime_start=obs_date,
            realtime_end=obs_date
        ))
    
    unrate_series = FREDSeries(
        series_id="UNRATE",
        title="Unemployment Rate",
        observations=unrate_observations,
        units="Percent",
        frequency="Monthly",
        last_updated=datetime.now()
    )
    
    # 非農就業數據 - 增長放緩
    payems_observations = []
    base_nfp = 157000  # 千人
    for i in range(3):
        month = today.month - i
        year = today.year
        if month <= 0:
            month += 12
            year -= 1
        obs_date = date(year, month, 1)
        value = base_nfp - i * 50  # 每月僅增加約 50K
        payems_observations.append(FREDObservation(
            date=obs_date,
            value=value,
            realtime_start=obs_date,
            realtime_end=obs_date
        ))
    
    payems_series = FREDSeries(
        series_id="PAYEMS",
        title="Non-Farm Payroll",
        observations=payems_observations,
        units="Thousands of Persons",
        frequency="Monthly",
        last_updated=datetime.now()
    )
    
    return {
        "CPIAUCSL": cpi_series,
        "UNRATE": unrate_series,
        "PAYEMS": payems_series
    }


# ============================================
# 測試函數
# ============================================

async def test_prompt_generation():
    """測試 1：Prompt 生成"""
    logger.info("=" * 60)
    logger.info("測試 1：Economic Agent Prompt 生成")
    logger.info("=" * 60)
    
    try:
        agent = EconAgent()
        
        # 準備測試數據
        data = {"fred_data": create_mock_fred_data_healthy()}
        
        # 生成 System Prompt
        system_prompt = agent.get_system_prompt()
        logger.info(f"System Prompt 長度: {len(system_prompt)} 字元")
        
        # 生成 User Prompt
        user_prompt = agent.format_user_prompt(data)
        logger.info(f"User Prompt 長度: {len(user_prompt)} 字元")
        
        # 驗證 Prompt 內容
        assert "通膨數據" in user_prompt
        assert "就業數據" in user_prompt
        assert "CPI" in user_prompt
        assert "失業率" in user_prompt
        
        logger.info("\n=== User Prompt 預覽 ===")
        logger.info(user_prompt[:600] + "...")
        
        logger.info("\n[OK] 測試 1 通過：Prompt 生成正確")
        return True
        
    except Exception as e:
        logger.error(f"[X] 測試 1 失敗: {str(e)}")
        return False


async def test_incomplete_data():
    """測試 2：數據不完整時的處理"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 2：數據不完整時的處理")
    logger.info("=" * 60)
    
    try:
        agent = EconAgent()
        
        # 僅提供部分數據
        partial_data = {
            "fred_data": {
                "CPIAUCSL": create_mock_fred_data_healthy()["CPIAUCSL"]
            }
        }
        
        user_prompt = agent.format_user_prompt(partial_data)
        
        # 應該顯示「無數據」
        assert "無數據" in user_prompt or "N/A" in user_prompt
        
        logger.info("Prompt 正確處理缺失數據")
        logger.info(f"數據完整性區塊存在: {'數據完整性' in user_prompt}")
        
        logger.info("\n[OK] 測試 2 通過：缺失數據處理正確")
        return True
        
    except Exception as e:
        logger.error(f"[X] 測試 2 失敗: {str(e)}")
        return False


async def test_output_model():
    """測試 3：輸出模型驗證"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 3：輸出模型驗證")
    logger.info("=" * 60)
    
    try:
        agent = EconAgent()
        output_model = agent.get_output_model()
        
        logger.info(f"輸出模型: {output_model.__name__}")
        
        # 驗證模型欄位
        model_fields = output_model.model_fields.keys()
        required_fields = [
            "soft_landing_score",
            "inflation_trend",
            "employment_status",
            "key_indicators",
            "summary",
            "confidence"
        ]
        
        for field in required_fields:
            if field in model_fields:
                logger.info(f"  [OK] 欄位存在: {field}")
            else:
                logger.error(f"  [X] 欄位缺失: {field}")
                return False
        
        logger.info("\n[OK] 測試 3 通過：輸出模型結構正確")
        return True
        
    except Exception as e:
        logger.error(f"[X] 測試 3 失敗: {str(e)}")
        return False


async def test_full_analysis_healthy():
    """測試 4：完整分析流程（健康數據）"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 4：完整分析流程 - 健康經濟數據")
    logger.info("=" * 60)
    
    if not settings.gemini_api_key:
        logger.warning("跳過測試 4：缺少 Gemini API Key")
        return None
    
    try:
        agent = EconAgent()
        
        # 準備完整數據
        data = {"fred_data": create_mock_fred_data_healthy()}
        
        logger.info("調用 LLM 進行分析（健康數據）...")
        result = await agent.analyze(data)
        
        if result:
            logger.info("\n=== 分析結果 ===")
            logger.info(f"軟著陸評分: {result.soft_landing_score:.1f}/10")
            logger.info(f"通膨趨勢: {result.inflation_trend}")
            logger.info(f"就業狀況: {result.employment_status}")
            logger.info(f"信心指數: {result.confidence:.2f}")
            logger.info(f"關鍵指標: {result.key_indicators}")
            logger.info(f"\n總結: {result.summary[:200]}...")
            
            # 健康數據應該得到較高的軟著陸評分
            if result.soft_landing_score >= 5.0:
                logger.info("[OK] 軟著陸評分符合預期（健康數據 >= 5.0）")
            else:
                logger.warning(f"[?] 軟著陸評分較低: {result.soft_landing_score}")
            
            logger.info("\n[OK] 測試 4 通過：完整分析成功")
            return True
        else:
            logger.warning("[?] 測試 4：分析返回 None（可能是 API 錯誤）")
            return False
        
    except Exception as e:
        logger.error(f"[X] 測試 4 失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_analysis_concerning():
    """測試 5：完整分析流程（令人擔憂數據）"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 5：完整分析流程 - 令人擔憂經濟數據")
    logger.info("=" * 60)
    
    if not settings.gemini_api_key:
        logger.warning("跳過測試 5：缺少 Gemini API Key")
        return None
    
    try:
        agent = EconAgent()
        
        # 準備令人擔憂數據
        data = {"fred_data": create_mock_fred_data_concerning()}
        
        logger.info("調用 LLM 進行分析（令人擔憂數據）...")
        result = await agent.analyze(data)
        
        if result:
            logger.info("\n=== 分析結果 ===")
            logger.info(f"軟著陸評分: {result.soft_landing_score:.1f}/10")
            logger.info(f"通膨趨勢: {result.inflation_trend}")
            logger.info(f"就業狀況: {result.employment_status}")
            logger.info(f"信心指數: {result.confidence:.2f}")
            logger.info(f"\n總結: {result.summary[:200]}...")
            
            logger.info("\n[OK] 測試 5 通過：完整分析成功")
            return True
        else:
            logger.warning("[?] 測試 5：分析返回 None")
            return False
        
    except Exception as e:
        logger.error(f"[X] 測試 5 失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================
# 主程式
# ============================================

async def main():
    """執行所有測試"""
    logger.info(">>> 開始測試 Economic Agent")
    logger.info("=" * 60)
    
    try:
        # 驗證配置
        validate_config()
        
        # 執行測試
        results = []
        
        # 測試 1-3 不需要 API
        results.append(("Prompt 生成", await test_prompt_generation()))
        results.append(("缺失數據處理", await test_incomplete_data()))
        results.append(("輸出模型", await test_output_model()))
        
        # 測試 4-5 需要 API
        healthy_result = await test_full_analysis_healthy()
        if healthy_result is not None:
            results.append(("完整分析（健康數據）", healthy_result))
        
        concerning_result = await test_full_analysis_concerning()
        if concerning_result is not None:
            results.append(("完整分析（擔憂數據）", concerning_result))
        
        # 總結
        logger.info("\n" + "=" * 60)
        logger.info("測試總結")
        logger.info("=" * 60)
        
        for test_name, passed in results:
            status = "[OK] 通過" if passed else "[X] 失敗"
            logger.info(f"{test_name}: {status}")
        
        total_passed = sum(1 for _, passed in results if passed)
        total_tests = len(results)
        
        logger.info("=" * 60)
        logger.info(f"總計：{total_passed}/{total_tests} 測試通過")
        
        if total_passed == total_tests:
            logger.info(">>> 所有測試通過！")
        else:
            logger.warning(">>> 部分測試失敗")
        
    except Exception as e:
        logger.error(f"[X] 測試執行失敗: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
