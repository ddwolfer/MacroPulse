"""
快速驗證 Sentiment Agent

不需要 API 的基礎驗證
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.sentiment_agent import SentimentAgent
from src.schema.models import PolymarketMarket, PolymarketToken


def create_mock_polymarket_data() -> list:
    """創建模擬的 Polymarket 市場數據"""
    return [
        PolymarketMarket(
            id="fed-rate-cut-jan",
            question="Will the Fed cut rates in January 2026?",
            slug="fed-rate-cut-jan-2026",
            category="Macro",
            volume=350000.0,
            liquidity=150000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="Yes", price=0.42, volume=175000.0),
                PolymarketToken(outcome="No", price=0.58, volume=175000.0)
            ],
            price_change_7d=0.08  # 上漲 8%
        ),
        PolymarketMarket(
            id="trump-win-2028",
            question="Will Trump win the 2028 election?",
            slug="trump-win-2028",
            category="Politics",
            volume=850000.0,
            liquidity=400000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="Yes", price=0.35, volume=425000.0),
                PolymarketToken(outcome="No", price=0.65, volume=425000.0)
            ],
            price_change_7d=-0.12  # 下跌 12%
        ),
        PolymarketMarket(
            id="btc-100k-2026",
            question="Will Bitcoin reach $100K by end of 2026?",
            slug="btc-100k-2026",
            category="Crypto",
            volume=520000.0,
            liquidity=200000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="Yes", price=0.65, volume=260000.0),
                PolymarketToken(outcome="No", price=0.35, volume=260000.0)
            ],
            price_change_7d=0.18  # 上漲 18%（劇烈變動）
        ),
        PolymarketMarket(
            id="recession-2026",
            question="Will the US enter recession in 2026?",
            slug="us-recession-2026",
            category="Macro",
            volume=280000.0,
            liquidity=120000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="Yes", price=0.28, volume=140000.0),
                PolymarketToken(outcome="No", price=0.72, volume=140000.0)
            ],
            price_change_7d=-0.05
        ),
        # 低交易量市場（應被過濾）
        PolymarketMarket(
            id="low-volume-market",
            question="Some low volume market?",
            slug="low-volume",
            category="Other",
            volume=50000.0,  # 低於門檻
            liquidity=20000.0,
            active=True,
            tokens=[
                PolymarketToken(outcome="Yes", price=0.50, volume=25000.0),
                PolymarketToken(outcome="No", price=0.50, volume=25000.0)
            ]
        ),
    ]


def test_sentiment_agent():
    """驗證 Sentiment Agent 基礎功能"""
    print("=" * 60)
    print("驗證 Sentiment Agent")
    print("=" * 60)
    
    # 測試 1：創建 Agent
    print("\n[測試 1] 創建 Sentiment Agent...")
    agent = SentimentAgent()
    print(f"  [OK] Agent 名稱: {agent.name}")
    print(f"  [OK] 溫度: {agent.temperature}")
    
    # 測試 2：System Prompt
    print("\n[測試 2] 獲取 System Prompt...")
    system_prompt = agent.get_system_prompt()
    print(f"  [OK] System Prompt 長度: {len(system_prompt)} 字元")
    assert "預測市場" in system_prompt or "Polymarket" in system_prompt
    assert "焦慮" in system_prompt or "情緒" in system_prompt
    print("  [OK] System Prompt 內容正確")
    
    # 測試 3：User Prompt 生成
    print("\n[測試 3] 生成 User Prompt...")
    mock_data = create_mock_polymarket_data()
    test_data = {"polymarket_data": mock_data}
    
    user_prompt = agent.format_user_prompt(test_data)
    print(f"  [OK] User Prompt 長度: {len(user_prompt)} 字元")
    
    # 檢查 Prompt 包含正確內容
    assert "高交易量市場" in user_prompt or "Volume" in user_prompt
    assert "Fed" in user_prompt  # 應該包含我們的模擬市場
    print("  [OK] User Prompt 包含必要內容")
    
    # 顯示 Prompt 預覽
    print("\n  --- User Prompt 預覽 ---")
    preview_lines = user_prompt.split("\n")[:20]
    for line in preview_lines:
        print(f"  {line}")
    print("  ...")
    
    # 測試 4：輸出模型
    print("\n[測試 4] 獲取輸出模型...")
    output_model = agent.get_output_model()
    print(f"  [OK] 輸出模型: {output_model.__name__}")
    
    # 驗證模型欄位
    expected_fields = [
        "market_anxiety_score",
        "key_events",
        "surprising_markets",
        "summary",
        "confidence"
    ]
    
    model_fields = list(output_model.model_fields.keys())
    for field in expected_fields:
        if field in model_fields:
            print(f"  [OK] 欄位存在: {field}")
        else:
            print(f"  [X] 欄位缺失: {field}")
            raise AssertionError(f"缺少欄位: {field}")
    
    # 測試 5：內部輔助函數
    print("\n[測試 5] 驗證輔助函數...")
    
    # 測試 _calculate_market_sentiment
    sentiment = agent._calculate_market_sentiment(mock_data)
    print(f"  [OK] _calculate_market_sentiment: {sentiment:.2f}")
    
    # 測試 _identify_surprising_markets
    surprising = agent._identify_surprising_markets(mock_data)
    print(f"  [OK] _identify_surprising_markets: {len(surprising)} 個")
    for s in surprising:
        print(f"       - {s[:60]}...")
    
    # 測試 6：空數據處理
    print("\n[測試 6] 測試空數據處理...")
    empty_data = {"polymarket_data": []}
    empty_prompt = agent.format_user_prompt(empty_data)
    assert "警告" in empty_prompt or "沒有" in empty_prompt
    print("  [OK] 空數據處理正確")
    
    # 總結
    print("\n" + "=" * 60)
    print(">>> 所有驗證通過!")
    print("=" * 60)
    print("\nSentiment Agent 準備就緒，可以開始分析。")
    print("\n提示：如要測試完整 LLM 分析，請執行:")
    print("  uv run python test_scripts/test_sentiment_agent.py")


if __name__ == "__main__":
    try:
        test_sentiment_agent()
    except Exception as e:
        print(f"\n[X] 驗證失敗: {str(e)}")
        import traceback
        traceback.print_exc()
