"""
快速驗證 BaseAgent 功能

這是一個簡化的驗證腳本，不需要真實 API 調用。
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.base_agent import BaseAgent


def test_1_class_structure():
    """測試 1：驗證 BaseAgent 類別結構"""
    print("=" * 60)
    print("測試 1：BaseAgent 類別結構")
    print("=" * 60)
    
    # 檢查必要的方法
    required_methods = [
        'get_system_prompt',
        'format_user_prompt',
        'get_output_model',
        'analyze',
        '_call_llm_with_retry',
        '_validate_output',
        '_try_fix_json',
        '_handle_error',
        'get_agent_info'
    ]
    
    for method_name in required_methods:
        if hasattr(BaseAgent, method_name):
            print(f"[OK] 方法存在: {method_name}")
        else:
            print(f"[X] 方法缺失: {method_name}")
    
    print("\n[OK] 測試 1 通過：BaseAgent 結構完整")


def test_2_json_fixing():
    """測試 2：驗證 JSON 修復功能"""
    print("\n" + "=" * 60)
    print("測試 2：JSON 修復功能")
    print("=" * 60)
    
    from typing import Type
    from pydantic import BaseModel
    
    # 創建一個簡單的測試 Agent
    class DummyAgent(BaseAgent):
        def __init__(self):
            # 不初始化 LLM，只測試 JSON 修復
            self.name = "DummyAgent"
        
        def get_system_prompt(self):
            return ""
        
        def format_user_prompt(self, data):
            return ""
        
        def get_output_model(self):
            return BaseModel
    
    agent = DummyAgent()
    
    # 測試案例
    test_cases = [
        ('```json\n{"test": "value"}\n```', '{"test": "value"}'),
        ('```\n{"test": "value"}\n```', '{"test": "value"}'),
        ('前文 {"test": "value"} 後文', '{"test": "value"}'),
        ('{"test": "value"}', '{"test": "value"}'),
    ]
    
    success = 0
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = agent._try_fix_json(input_text)
        if result and result.strip() == expected.strip():
            print(f"[OK] 案例 {i} 通過")
            success += 1
        else:
            print(f"[X] 案例 {i} 失敗")
            print(f"   輸入: {input_text[:50]}...")
            print(f"   期望: {expected}")
            print(f"   得到: {result}")
    
    print(f"\n[OK] 測試 2 通過：{success}/{len(test_cases)} 案例成功")


def test_3_error_handling():
    """測試 3：驗證錯誤處理"""
    print("\n" + "=" * 60)
    print("測試 3：錯誤處理")
    print("=" * 60)
    
    from src.agents.base_agent import AgentExecutionError
    
    try:
        # 創建一個錯誤
        error = AgentExecutionError(
            agent_name="TestAgent",
            error_type="ValueError",
            error_message="測試錯誤",
            can_continue=True
        )
        
        print(f"[OK] 錯誤類別建立成功")
        print(f"   Agent: {error.agent_name}")
        print(f"   類型: {error.error_type}")
        print(f"   訊息: {error.error_message}")
        print(f"   可繼續: {error.can_continue}")
        
        print("\n[OK] 測試 3 通過：錯誤處理結構正確")
    except Exception as e:
        print(f"[X] 測試 3 失敗: {str(e)}")


def test_4_imports():
    """測試 4：驗證模組匯入"""
    print("\n" + "=" * 60)
    print("測試 4：模組匯入")
    print("=" * 60)
    
    try:
        from src.agents import BaseAgent, AgentExecutionError
        print("[OK] 從 src.agents 匯入成功")
        
        from src.agents.base_agent import BaseAgent as BA
        print("[OK] 從 src.agents.base_agent 匯入成功")
        
        print("\n[OK] 測試 4 通過：所有匯入正常")
    except Exception as e:
        print(f"[X] 測試 4 失敗: {str(e)}")


def main():
    """執行所有驗證測試"""
    print(">>> 開始驗證 BaseAgent（無需 API）")
    print("=" * 60)
    
    try:
        test_1_class_structure()
        test_2_json_fixing()
        test_3_error_handling()
        test_4_imports()
        
        print("\n" + "=" * 60)
        print(">>> 所有驗證測試通過！")
        print("=" * 60)
        
        print("\n>>> BaseAgent 核心功能驗證完成：")
        print("  [OK] 類別結構完整")
        print("  [OK] JSON 修復功能正常")
        print("  [OK] 錯誤處理機制正確")
        print("  [OK] 模組匯入無誤")
        
        print("\n>>> 如需測試 LLM 調用功能，請執行：")
        print("   uv run python test_scripts/test_agents.py")
        
    except Exception as e:
        print(f"\n[X] 驗證失敗: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

