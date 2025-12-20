"""
測試 Fed Agent 功能

驗證貨幣政策分析 Agent 的 Prompt 生成、數據處理和 LLM 調用。
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings, validate_config
from src.agents.fed_agent import FedAgent
from src.schema.models import TreasuryYield, PolymarketMarket, PolymarketToken
from src.utils.logger import setup_logger

# 設定日誌
setup_logger("MacroPulse", settings.log_level)
logger = logging.getLogger(__name__)


# ============================================
# 測試數據準備
# ============================================

def create_mock_treasury_data() -> list:
    """創建模擬的美債殖利率數據"""
    return [
        TreasuryYield(
            symbol="^IRX",
            maturity="3M",
            yield_value=5.25,
            timestamp=datetime.now()
        ),
        TreasuryYield(
            symbol="^FVX",
            maturity="5Y",
            yield_value=4.15,
            timestamp=datetime.now()
        ),
        TreasuryYield(
            symbol="^TNX",
            maturity="10Y",
            yield_value=4.25,
            timestamp=datetime.now()
        ),
        TreasuryYield(
            symbol="^TYX",
            maturity="30Y",
            yield_value=4.45,
            timestamp=datetime.now()
        ),
    ]


def create_mock_treasury_data_inverted() -> list:
    """創建倒掛的美債殖利率數據"""
    return [
        TreasuryYield(
            symbol="^IRX",
            maturity="2Y",
            yield_value=4.85,
            timestamp=datetime.now()
        ),
        TreasuryYield(
            symbol="^TNX",
            maturity="10Y",
            yield_value=4.25,  # 低於 2Y，形成倒掛
            timestamp=datetime.now()
        ),
    ]


def create_mock_fedwatch_data() -> dict:
    """創建模擬的 FedWatch 數據"""
    return {
        "cut_probability": 65,
        "hold_probability": 30,
        "hike_probability": 5
    }


def create_mock_polymarket_data() -> list:
    """創建模擬的 Polymarket 數據"""
    return [
        PolymarketMarket(
            id="fed-rate-cut-jan",
            question="Will the Fed cut rates in January 2025?",
            slug="fed-rate-cut-jan-2025",
            category="Macro",
            volume=250000.0,
            liquidity=100000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="Yes", price=0.42, volume=125000.0),
                PolymarketToken(outcome="No", price=0.58, volume=125000.0)
            ]
        ),
        PolymarketMarket(
            id="fed-total-cuts-2025",
            question="How many rate cuts will the Fed make in 2025?",
            slug="fed-rate-cuts-2025",
            category="Macro",
            volume=180000.0,
            liquidity=80000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="3+ cuts", price=0.35, volume=90000.0),
                PolymarketToken(outcome="<3 cuts", price=0.65, volume=90000.0)
            ]
        ),
    ]


# ============================================
# 測試函數
# ============================================

async def test_prompt_generation():
    """測試 1：Prompt 生成"""
    logger.info("=" * 60)
    logger.info("測試 1：Fed Agent Prompt 生成")
    logger.info("=" * 60)
    
    try:
        agent = FedAgent()
        
        # 準備測試數據
        data = {
            "treasury_yields": create_mock_treasury_data(),
            "fedwatch_data": create_mock_fedwatch_data(),
            "polymarket_data": create_mock_polymarket_data()
        }
        
        # 生成 System Prompt
        system_prompt = agent.get_system_prompt()
        logger.info(f"System Prompt 長度: {len(system_prompt)} 字元")
        
        # 生成 User Prompt
        user_prompt = agent.format_user_prompt(data)
        logger.info(f"User Prompt 長度: {len(user_prompt)} 字元")
        
        # 驗證 Prompt 內容
        assert "貨幣政策" in user_prompt
        assert "殖利率" in user_prompt
        assert "FedWatch" in user_prompt
        assert "Polymarket" in user_prompt
        
        logger.info("\n=== User Prompt 預覽 ===")
        logger.info(user_prompt[:500] + "...")
        
        logger.info("\n[OK] 測試 1 通過：Prompt 生成正確")
        return True
        
    except Exception as e:
        logger.error(f"[X] 測試 1 失敗: {str(e)}")
        return False


async def test_inverted_yield_curve():
    """測試 2：倒掛檢測"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 2：殖利率曲線倒掛檢測")
    logger.info("=" * 60)
    
    try:
        agent = FedAgent()
        
        # 使用倒掛數據
        data = {
            "treasury_yields": create_mock_treasury_data_inverted()
        }
        
        user_prompt = agent.format_user_prompt(data)
        
        # 驗證倒掛警告
        assert "倒掛" in user_prompt or "警告" in user_prompt
        
        logger.info("檢測到倒掛警告：")
        if "***" in user_prompt:
            warning_lines = [line for line in user_prompt.split("\n") if "***" in line]
            for line in warning_lines:
                logger.info(f"  {line}")
        
        logger.info("\n[OK] 測試 2 通過：倒掛檢測正常")
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
        agent = FedAgent()
        output_model = agent.get_output_model()
        
        logger.info(f"輸出模型: {output_model.__name__}")
        
        # 驗證模型欄位
        model_fields = output_model.model_fields.keys()
        required_fields = [
            "tone_index",
            "key_risks",
            "summary",
            "confidence",
            "yield_curve_status",
            "next_fomc_probability"
        ]
        
        for field in required_fields:
            if field in model_fields:
                logger.info(f"[OK] 欄位存在: {field}")
            else:
                logger.error(f"[X] 欄位缺失: {field}")
                return False
        
        logger.info("\n[OK] 測試 3 通過：輸出模型結構正確")
        return True
        
    except Exception as e:
        logger.error(f"[X] 測試 3 失敗: {str(e)}")
        return False


async def test_full_analysis():
    """測試 4：完整分析流程（需要 API）"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 4：完整分析流程（需要 Gemini API）")
    logger.info("=" * 60)
    
    if not settings.gemini_api_key:
        logger.warning("跳過測試 4：缺少 Gemini API Key")
        return None
    
    try:
        agent = FedAgent()
        
        # 準備完整數據
        data = {
            "treasury_yields": create_mock_treasury_data(),
            "fedwatch_data": create_mock_fedwatch_data(),
            "polymarket_data": create_mock_polymarket_data()
        }
        
        logger.info("調用 LLM 進行分析...")
        result = await agent.analyze(data)
        
        if result:
            logger.info("\n=== 分析結果 ===")
            logger.info(f"鷹/鴿指數: {result.tone_index:.2f}")
            logger.info(f"曲線狀態: {result.yield_curve_status}")
            logger.info(f"信心指數: {result.confidence:.2f}")
            logger.info(f"關鍵風險數: {len(result.key_risks)}")
            logger.info(f"\n總結: {result.summary[:150]}...")
            
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


# ============================================
# 主程式
# ============================================

async def main():
    """執行所有測試"""
    logger.info(">>> 開始測試 Fed Agent")
    logger.info("=" * 60)
    
    try:
        # 驗證配置
        validate_config()
        
        # 執行測試
        results = []
        
        # 測試 1-3 不需要 API
        results.append(("Prompt 生成", await test_prompt_generation()))
        results.append(("倒掛檢測", await test_inverted_yield_curve()))
        results.append(("輸出模型", await test_output_model()))
        
        # 測試 4 需要 API
        full_analysis_result = await test_full_analysis()
        if full_analysis_result is not None:
            results.append(("完整分析", full_analysis_result))
        
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

