"""
快速驗證 Correlation Agent

不需要 API 的基礎驗證
"""

import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.correlation_agent import CorrelationAgent
from src.schema.models import AssetPriceHistory, UserPortfolio


def create_mock_asset_prices() -> dict:
    """創建模擬的資產價格歷史"""
    today = date.today()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    
    return {
        "BTC-USD": AssetPriceHistory(
            symbol="BTC-USD",
            prices=[42000, 42500, 43000, 42800, 43500, 44000, 44500],
            dates=dates
        ),
        "ETH-USD": AssetPriceHistory(
            symbol="ETH-USD",
            prices=[2200, 2250, 2300, 2280, 2350, 2400, 2450],
            dates=dates
        ),
        "SPY": AssetPriceHistory(
            symbol="SPY",
            prices=[470, 472, 475, 473, 478, 480, 482],
            dates=dates
        ),
        "QQQ": AssetPriceHistory(
            symbol="QQQ",
            prices=[400, 403, 408, 405, 412, 415, 418],
            dates=dates
        ),
        "DX-Y.NYB": AssetPriceHistory(
            symbol="DX-Y.NYB",
            prices=[104.5, 104.2, 103.8, 104.0, 103.5, 103.2, 103.0],  # DXY 下跌
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


def test_correlation_agent():
    """驗證 Correlation Agent 基礎功能"""
    print("=" * 60)
    print("驗證 Correlation Agent")
    print("=" * 60)
    
    # 測試 1：創建 Agent
    print("\n[測試 1] 創建 Correlation Agent...")
    agent = CorrelationAgent()
    print(f"  [OK] Agent 名稱: {agent.name}")
    print(f"  [OK] 溫度: {agent.temperature}")
    
    # 測試 2：System Prompt
    print("\n[測試 2] 獲取 System Prompt...")
    system_prompt = agent.get_system_prompt()
    print(f"  [OK] System Prompt 長度: {len(system_prompt)} 字元")
    assert "相關係數" in system_prompt or "correlation" in system_prompt.lower()
    assert "BTC" in system_prompt
    print("  [OK] System Prompt 內容正確")
    
    # 測試 3：User Prompt 生成（無持倉）
    print("\n[測試 3] 生成 User Prompt（無持倉）...")
    mock_prices = create_mock_asset_prices()
    test_data = {"asset_prices": mock_prices}
    
    user_prompt = agent.format_user_prompt(test_data)
    print(f"  [OK] User Prompt 長度: {len(user_prompt)} 字元")
    
    # 檢查 Prompt 包含正確內容
    assert "BTC-USD" in user_prompt or "BTC" in user_prompt
    assert "相關係數" in user_prompt
    print("  [OK] User Prompt 包含必要內容")
    
    # 顯示 Prompt 預覽
    print("\n  --- User Prompt 預覽 ---")
    preview_lines = user_prompt.split("\n")[:20]
    for line in preview_lines:
        print(f"  {line}")
    print("  ...")
    
    # 測試 4：User Prompt 生成（含持倉）
    print("\n[測試 4] 生成 User Prompt（含持倉）...")
    test_data_with_portfolio = {
        "asset_prices": mock_prices,
        "user_portfolio": create_mock_user_portfolio()
    }
    
    user_prompt_portfolio = agent.format_user_prompt(test_data_with_portfolio)
    assert "用戶持倉" in user_prompt_portfolio or "持倉" in user_prompt_portfolio
    print(f"  [OK] User Prompt 包含持倉資訊")
    
    # 測試 5：輸出模型
    print("\n[測試 5] 獲取輸出模型...")
    output_model = agent.get_output_model()
    print(f"  [OK] 輸出模型: {output_model.__name__}")
    
    # 驗證模型欄位
    expected_fields = [
        "correlation_matrix",
        "risk_warnings",
        "portfolio_impact",
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
    
    # 測試 6：內部輔助函數
    print("\n[測試 6] 驗證輔助函數...")
    
    # 測試 _calculate_correlation_matrix
    corr_matrix = agent._calculate_correlation_matrix(mock_prices)
    print(f"  [OK] _calculate_correlation_matrix: {len(corr_matrix)} 對")
    for pair, corr in list(corr_matrix.items())[:3]:
        print(f"       - {pair}: {corr:.2f}")
    
    # 測試 _get_correlation_strength
    strength = agent._get_correlation_strength(0.8)
    print(f"  [OK] _get_correlation_strength(0.8): {strength}")
    
    # 測試 7：空數據處理
    print("\n[測試 7] 測試空數據處理...")
    empty_data = {"asset_prices": {}}
    empty_prompt = agent.format_user_prompt(empty_data)
    assert "警告" in empty_prompt or "沒有" in empty_prompt
    print("  [OK] 空數據處理正確")
    
    # 總結
    print("\n" + "=" * 60)
    print(">>> 所有驗證通過!")
    print("=" * 60)
    print("\nCorrelation Agent 準備就緒，可以開始分析。")
    print("\n提示：如要測試完整 LLM 分析，請執行:")
    print("  uv run python test_scripts/test_correlation_agent.py")


if __name__ == "__main__":
    try:
        test_correlation_agent()
    except Exception as e:
        print(f"\n[X] 驗證失敗: {str(e)}")
        import traceback
        traceback.print_exc()
