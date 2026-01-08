"""
測試 Correlation Agent 功能

驗證資產連動分析 Agent 的 Prompt 生成、數據處理和 LLM 調用。
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import date, timedelta

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings, validate_config
from src.agents.correlation_agent import CorrelationAgent
from src.schema.models import AssetPriceHistory, UserPortfolio
from src.utils.logger import setup_logger

# 設定日誌
setup_logger("MacroPulse", settings.log_level)
logger = logging.getLogger(__name__)


# ============================================
# 測試數據準備
# ============================================

def create_mock_asset_prices_bullish() -> dict:
    """創建模擬的看漲市場數據（BTC 與 QQQ 高度正相關）"""
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    
    return {
        "BTC-USD": AssetPriceHistory(
            symbol="BTC-USD",
            prices=[42000, 43000, 44500, 45000, 46000, 47000, 48000],  # 上漲趨勢
            dates=dates
        ),
        "ETH-USD": AssetPriceHistory(
            symbol="ETH-USD",
            prices=[2200, 2280, 2380, 2420, 2500, 2580, 2650],  # 上漲趨勢
            dates=dates
        ),
        "SPY": AssetPriceHistory(
            symbol="SPY",
            prices=[470, 473, 478, 480, 485, 488, 492],  # 上漲趨勢
            dates=dates
        ),
        "QQQ": AssetPriceHistory(
            symbol="QQQ",
            prices=[400, 405, 412, 418, 425, 430, 438],  # 上漲趨勢
            dates=dates
        ),
        "DX-Y.NYB": AssetPriceHistory(
            symbol="DX-Y.NYB",
            prices=[104.5, 104.0, 103.5, 103.2, 102.8, 102.5, 102.0],  # 下跌趨勢
            dates=dates
        ),
    }


def create_mock_asset_prices_bearish() -> dict:
    """創建模擬的看跌市場數據（DXY 上漲，風險資產下跌）"""
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    
    return {
        "BTC-USD": AssetPriceHistory(
            symbol="BTC-USD",
            prices=[48000, 47000, 45500, 44000, 43000, 42000, 41000],  # 下跌趨勢
            dates=dates
        ),
        "ETH-USD": AssetPriceHistory(
            symbol="ETH-USD",
            prices=[2650, 2550, 2450, 2380, 2300, 2250, 2180],  # 下跌趨勢
            dates=dates
        ),
        "SPY": AssetPriceHistory(
            symbol="SPY",
            prices=[492, 488, 483, 478, 475, 472, 468],  # 下跌趨勢
            dates=dates
        ),
        "QQQ": AssetPriceHistory(
            symbol="QQQ",
            prices=[438, 430, 420, 412, 405, 400, 395],  # 下跌趨勢
            dates=dates
        ),
        "DX-Y.NYB": AssetPriceHistory(
            symbol="DX-Y.NYB",
            prices=[102.0, 102.5, 103.0, 103.5, 104.0, 104.5, 105.0],  # 上漲趨勢
            dates=dates
        ),
    }


def create_mock_user_portfolio() -> UserPortfolio:
    """創建模擬的用戶持倉"""
    return UserPortfolio(
        holdings=[
            {"symbol": "BTC-USD", "quantity": 1.5},
            {"symbol": "ETH-USD", "quantity": 10.0},
            {"symbol": "QQQ", "quantity": 50}
        ]
    )


# ============================================
# 測試函數
# ============================================

async def test_prompt_generation():
    """測試 1：Prompt 生成"""
    logger.info("=" * 60)
    logger.info("測試 1：Correlation Agent Prompt 生成")
    logger.info("=" * 60)
    
    try:
        agent = CorrelationAgent()
        
        # 準備測試數據
        data = {"asset_prices": create_mock_asset_prices_bullish()}
        
        # 生成 System Prompt
        system_prompt = agent.get_system_prompt()
        logger.info(f"System Prompt 長度: {len(system_prompt)} 字元")
        
        # 生成 User Prompt
        user_prompt = agent.format_user_prompt(data)
        logger.info(f"User Prompt 長度: {len(user_prompt)} 字元")
        
        # 驗證 Prompt 內容
        assert "相關係數" in user_prompt or "BTC" in user_prompt
        
        logger.info("\n=== User Prompt 預覽 ===")
        logger.info(user_prompt[:600] + "...")
        
        logger.info("\n[OK] 測試 1 通過：Prompt 生成正確")
        return True
        
    except Exception as e:
        logger.error(f"[X] 測試 1 失敗: {str(e)}")
        return False


async def test_correlation_calculation():
    """測試 2：相關係數計算"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 2：相關係數計算")
    logger.info("=" * 60)
    
    try:
        agent = CorrelationAgent()
        
        # 計算相關係數
        asset_prices = create_mock_asset_prices_bullish()
        corr_matrix = agent._calculate_correlation_matrix(asset_prices)
        
        logger.info(f"計算出 {len(corr_matrix)} 對相關係數:")
        for pair, corr in corr_matrix.items():
            strength = agent._get_correlation_strength(corr)
            logger.info(f"  {pair}: {corr:.3f} ({strength})")
        
        # 驗證 BTC 與 QQQ 應該正相關（因為我們的模擬數據都是上漲）
        btc_qqq = [v for k, v in corr_matrix.items() if "BTC" in k and "QQQ" in k]
        if btc_qqq:
            assert btc_qqq[0] > 0.5, "BTC-QQQ 應該正相關"
            logger.info(f"  BTC-QQQ 正相關驗證通過: {btc_qqq[0]:.3f}")
        
        logger.info("\n[OK] 測試 2 通過：相關係數計算正確")
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
        agent = CorrelationAgent()
        output_model = agent.get_output_model()
        
        logger.info(f"輸出模型: {output_model.__name__}")
        
        # 驗證模型欄位
        model_fields = output_model.model_fields.keys()
        required_fields = [
            "correlation_matrix",
            "risk_warnings",
            "portfolio_impact",
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


async def test_full_analysis_bullish():
    """測試 4：完整分析流程（看漲數據）"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 4：完整分析流程 - 看漲市場數據")
    logger.info("=" * 60)
    
    if not settings.gemini_api_key:
        logger.warning("跳過測試 4：缺少 Gemini API Key")
        return None
    
    try:
        agent = CorrelationAgent()
        
        # 準備看漲數據
        data = {
            "asset_prices": create_mock_asset_prices_bullish(),
            "user_portfolio": create_mock_user_portfolio()
        }
        
        logger.info("調用 LLM 進行分析（看漲數據）...")
        result = await agent.analyze(data)
        
        if result:
            logger.info("\n=== 分析結果 ===")
            logger.info(f"相關係數對數: {len(result.correlation_matrix)}")
            logger.info(f"風險預警數: {len(result.risk_warnings)}")
            logger.info(f"持倉影響: {result.portfolio_impact}")
            logger.info(f"信心指數: {result.confidence:.2f}")
            logger.info(f"\n總結: {result.summary[:200]}...")
            
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


async def test_full_analysis_bearish():
    """測試 5：完整分析流程（看跌數據）"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 5：完整分析流程 - 看跌市場數據")
    logger.info("=" * 60)
    
    if not settings.gemini_api_key:
        logger.warning("跳過測試 5：缺少 Gemini API Key")
        return None
    
    try:
        agent = CorrelationAgent()
        
        # 準備看跌數據
        data = {
            "asset_prices": create_mock_asset_prices_bearish(),
            "user_portfolio": create_mock_user_portfolio()
        }
        
        logger.info("調用 LLM 進行分析（看跌數據）...")
        result = await agent.analyze(data)
        
        if result:
            logger.info("\n=== 分析結果 ===")
            logger.info(f"風險預警數: {len(result.risk_warnings)}")
            for warning in result.risk_warnings[:3]:
                logger.info(f"  - {warning}")
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
    logger.info(">>> 開始測試 Correlation Agent")
    logger.info("=" * 60)
    
    try:
        # 驗證配置
        validate_config()
        
        # 執行測試
        results = []
        
        # 測試 1-3 不需要 API
        results.append(("Prompt 生成", await test_prompt_generation()))
        results.append(("相關係數計算", await test_correlation_calculation()))
        results.append(("輸出模型", await test_output_model()))
        
        # 測試 4-5 需要 API
        bullish_result = await test_full_analysis_bullish()
        if bullish_result is not None:
            results.append(("完整分析（看漲數據）", bullish_result))
        
        bearish_result = await test_full_analysis_bearish()
        if bearish_result is not None:
            results.append(("完整分析（看跌數據）", bearish_result))
        
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
