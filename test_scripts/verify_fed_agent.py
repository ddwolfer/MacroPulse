"""
快速驗證 Fed Agent

不需要 API 的基礎驗證
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.fed_agent import FedAgent
from src.schema.models import TreasuryYield


def test_fed_agent():
    """驗證 Fed Agent 基礎功能"""
    print("=" * 60)
    print("驗證 Fed Agent")
    print("=" * 60)
    
    # 測試 1：創建 Agent
    print("\n[測試 1] 創建 Fed Agent...")
    agent = FedAgent()
    print(f"[OK] Agent 名稱: {agent.name}")
    print(f"[OK] 溫度: {agent.temperature}")
    
    # 測試 2：System Prompt
    print("\n[測試 2] 獲取 System Prompt...")
    system_prompt = agent.get_system_prompt()
    print(f"[OK] System Prompt 長度: {len(system_prompt)} 字元")
    assert "聯準會" in system_prompt
    assert "鷹" in system_prompt or "鴿" in system_prompt
    print("[OK] System Prompt 內容正確")
    
    # 測試 3：User Prompt 生成
    print("\n[測試 3] 生成 User Prompt...")
    test_data = {
        "treasury_yields": [
            TreasuryYield(
                symbol="^TNX",
                maturity="2Y",
                yield_value=4.50,
                timestamp=datetime.now()
            ),
            TreasuryYield(
                symbol="^TNX",
                maturity="10Y",
                yield_value=4.25,  # 倒掛
                timestamp=datetime.now()
            ),
        ]
    }
    
    user_prompt = agent.format_user_prompt(test_data)
    print(f"[OK] User Prompt 長度: {len(user_prompt)} 字元")
    
    # 檢查倒掛警告
    if "倒掛" in user_prompt or "警告" in user_prompt:
        print("[OK] 偵測到倒掛警告")
    
    # 測試 4：輸出模型
    print("\n[測試 4] 獲取輸出模型...")
    output_model = agent.get_output_model()
    print(f"[OK] 輸出模型: {output_model.__name__}")
    
    # 驗證模型欄位
    fields = list(output_model.model_fields.keys())
    print(f"[OK] 模型欄位: {', '.join(fields[:3])}...")
    
    # 總結
    print("\n" + "=" * 60)
    print(">>> 所有驗證通過!")
    print("=" * 60)
    print("\nFed Agent 準備就緒，可以開始分析。")
    print("\n提示：如要測試完整 LLM 分析，請執行:")
    print("  uv run python test_scripts/test_fed_agent.py")


if __name__ == "__main__":
    try:
        test_fed_agent()
    except Exception as e:
        print(f"\n[X] 驗證失敗: {str(e)}")
        import traceback
        traceback.print_exc()

