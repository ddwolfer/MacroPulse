"""
測試 Sentiment Agent 功能

驗證預測市場分析 Agent 的 Prompt 生成、數據處理和 LLM 調用。
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings, validate_config
from src.agents.sentiment_agent import SentimentAgent
from src.schema.models import PolymarketMarket, PolymarketToken
from src.utils.logger import setup_logger

# 設定日誌
setup_logger("MacroPulse", settings.log_level)
logger = logging.getLogger(__name__)


# ============================================
# 測試數據準備
# ============================================

def create_mock_polymarket_data_bullish() -> list:
    """創建模擬的樂觀市場數據"""
    return [
        PolymarketMarket(
            id="fed-rate-cut",
            question="Will the Fed cut rates in Q1 2026?",
            slug="fed-rate-cut-q1-2026",
            category="Macro",
            volume=450000.0,
            liquidity=200000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="Yes", price=0.72, volume=225000.0),
                PolymarketToken(outcome="No", price=0.28, volume=225000.0)
            ],
            price_change_7d=0.15  # 上漲 15%
        ),
        PolymarketMarket(
            id="btc-100k",
            question="Will Bitcoin reach $100K in 2026?",
            slug="btc-100k-2026",
            category="Crypto",
            volume=680000.0,
            liquidity=300000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="Yes", price=0.68, volume=340000.0),
                PolymarketToken(outcome="No", price=0.32, volume=340000.0)
            ],
            price_change_7d=0.22  # 上漲 22%（劇烈）
        ),
        PolymarketMarket(
            id="no-recession",
            question="Will the US avoid recession in 2026?",
            slug="us-no-recession-2026",
            category="Macro",
            volume=320000.0,
            liquidity=150000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="Yes", price=0.78, volume=160000.0),
                PolymarketToken(outcome="No", price=0.22, volume=160000.0)
            ],
            price_change_7d=0.08
        ),
    ]


def create_mock_polymarket_data_bearish() -> list:
    """創建模擬的悲觀市場數據"""
    return [
        PolymarketMarket(
            id="fed-hold",
            question="Will the Fed hold rates through Q2 2026?",
            slug="fed-hold-q2-2026",
            category="Macro",
            volume=380000.0,
            liquidity=180000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="Yes", price=0.65, volume=190000.0),
                PolymarketToken(outcome="No", price=0.35, volume=190000.0)
            ],
            price_change_7d=0.12  # 上漲（對股市不利）
        ),
        PolymarketMarket(
            id="recession-risk",
            question="Will the US enter recession in 2026?",
            slug="us-recession-2026",
            category="Macro",
            volume=520000.0,
            liquidity=250000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="Yes", price=0.42, volume=260000.0),
                PolymarketToken(outcome="No", price=0.58, volume=260000.0)
            ],
            price_change_7d=0.18  # 上漲（衰退機率上升）
        ),
        PolymarketMarket(
            id="market-crash",
            question="Will S&P 500 drop 20% in 2026?",
            slug="sp500-crash-2026",
            category="Macro",
            volume=280000.0,
            liquidity=120000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="Yes", price=0.25, volume=140000.0),
                PolymarketToken(outcome="No", price=0.75, volume=140000.0)
            ],
            price_change_7d=0.10  # 崩盤機率上升
        ),
    ]


# ============================================
# 測試函數
# ============================================

async def test_prompt_generation():
    """測試 1：Prompt 生成"""
    logger.info("=" * 60)
    logger.info("測試 1：Sentiment Agent Prompt 生成")
    logger.info("=" * 60)
    
    try:
        agent = SentimentAgent()
        
        # 準備測試數據
        data = {"polymarket_data": create_mock_polymarket_data_bullish()}
        
        # 生成 System Prompt
        system_prompt = agent.get_system_prompt()
        logger.info(f"System Prompt 長度: {len(system_prompt)} 字元")
        
        # 生成 User Prompt
        user_prompt = agent.format_user_prompt(data)
        logger.info(f"User Prompt 長度: {len(user_prompt)} 字元")
        
        # 驗證 Prompt 內容
        assert "高交易量市場" in user_prompt or "Market" in user_prompt
        assert "Fed" in user_prompt or "Bitcoin" in user_prompt
        
        logger.info("\n=== User Prompt 預覽 ===")
        logger.info(user_prompt[:600] + "...")
        
        logger.info("\n[OK] 測試 1 通過：Prompt 生成正確")
        return True
        
    except Exception as e:
        logger.error(f"[X] 測試 1 失敗: {str(e)}")
        return False


async def test_empty_data():
    """測試 2：空數據處理"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 2：空數據處理")
    logger.info("=" * 60)
    
    try:
        agent = SentimentAgent()
        
        # 空數據
        data = {"polymarket_data": []}
        
        user_prompt = agent.format_user_prompt(data)
        
        # 應該包含警告
        assert "警告" in user_prompt or "沒有" in user_prompt
        
        logger.info("Prompt 正確處理空數據")
        logger.info(f"Prompt 內容: {user_prompt[:200]}...")
        
        logger.info("\n[OK] 測試 2 通過：空數據處理正確")
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
        agent = SentimentAgent()
        output_model = agent.get_output_model()
        
        logger.info(f"輸出模型: {output_model.__name__}")
        
        # 驗證模型欄位
        model_fields = output_model.model_fields.keys()
        required_fields = [
            "market_anxiety_score",
            "key_events",
            "surprising_markets",
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
    """測試 4：完整分析流程（樂觀數據）"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 4：完整分析流程 - 樂觀市場數據")
    logger.info("=" * 60)
    
    if not settings.gemini_api_key:
        logger.warning("跳過測試 4：缺少 Gemini API Key")
        return None
    
    try:
        agent = SentimentAgent()
        
        # 準備樂觀數據
        data = {"polymarket_data": create_mock_polymarket_data_bullish()}
        
        logger.info("調用 LLM 進行分析（樂觀數據）...")
        result = await agent.analyze(data)
        
        if result:
            logger.info("\n=== 分析結果 ===")
            logger.info(f"市場焦慮度: {result.market_anxiety_score:.2f}")
            logger.info(f"關鍵事件數: {len(result.key_events)}")
            logger.info(f"驚訝市場數: {len(result.surprising_markets)}")
            logger.info(f"信心指數: {result.confidence:.2f}")
            logger.info(f"\n總結: {result.summary[:200]}...")
            
            # 樂觀數據應該得到負值或接近 0 的焦慮度
            logger.info(f"\n焦慮度分析: {result.market_anxiety_score:.2f} (樂觀數據預期 <= 0.3)")
            
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
    """測試 5：完整分析流程（悲觀數據）"""
    logger.info("\n" + "=" * 60)
    logger.info("測試 5：完整分析流程 - 悲觀市場數據")
    logger.info("=" * 60)
    
    if not settings.gemini_api_key:
        logger.warning("跳過測試 5：缺少 Gemini API Key")
        return None
    
    try:
        agent = SentimentAgent()
        
        # 準備悲觀數據
        data = {"polymarket_data": create_mock_polymarket_data_bearish()}
        
        logger.info("調用 LLM 進行分析（悲觀數據）...")
        result = await agent.analyze(data)
        
        if result:
            logger.info("\n=== 分析結果 ===")
            logger.info(f"市場焦慮度: {result.market_anxiety_score:.2f}")
            logger.info(f"關鍵事件數: {len(result.key_events)}")
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
    logger.info(">>> 開始測試 Sentiment Agent")
    logger.info("=" * 60)
    
    try:
        # 驗證配置
        validate_config()
        
        # 執行測試
        results = []
        
        # 測試 1-3 不需要 API
        results.append(("Prompt 生成", await test_prompt_generation()))
        results.append(("空數據處理", await test_empty_data()))
        results.append(("輸出模型", await test_output_model()))
        
        # 測試 4-5 需要 API
        bullish_result = await test_full_analysis_bullish()
        if bullish_result is not None:
            results.append(("完整分析（樂觀數據）", bullish_result))
        
        bearish_result = await test_full_analysis_bearish()
        if bearish_result is not None:
            results.append(("完整分析（悲觀數據）", bearish_result))
        
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
