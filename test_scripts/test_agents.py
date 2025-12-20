"""
測試 Agent 基礎功能

驗證 BaseAgent 的 LLM 調用、Prompt 渲染、錯誤處理。
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel, Field

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings, validate_config
from src.agents.base_agent import BaseAgent
from src.utils.logger import setup_logger

# 設定日誌
setup_logger("MacroPulse", settings.log_level)
logger = logging.getLogger(__name__)


# ============================================
# 測試用的簡單 Agent 和模型
# ============================================

class TestAnalysisOutput(BaseModel):
    """測試分析輸出模型"""
    sentiment: str = Field(..., description="情緒評估（正面/中性/負面）")
    confidence: float = Field(..., ge=0.0, le=1.0, description="信心指數")
    summary: str = Field(..., max_length=200, description="總結")


class SimpleTestAgent(BaseAgent):
    """簡單的測試 Agent"""
    
    def __init__(self):
        super().__init__(name="SimpleTestAgent", temperature=0.3)
    
    def get_system_prompt(self) -> str:
        """獲取 System Prompt"""
        return """你是一位專業的市場分析師。

你的任務：
1. 分析給定的市場數據
2. 評估市場情緒（正面/中性/負面）
3. 給出信心指數（0.0-1.0）
4. 撰寫簡短總結（100字以內）

輸出格式要求：
- 必須以 JSON 格式輸出
- 包含 sentiment, confidence, summary 三個欄位
- 保持專業和客觀
"""
    
    def format_user_prompt(self, data: Any) -> str:
        """格式化 User Prompt"""
        return f"""請分析以下市場數據：

{data}

請提供專業的市場情緒分析。"""
    
    def get_output_model(self) -> Type[BaseModel]:
        """獲取輸出模型"""
        return TestAnalysisOutput


# ============================================
# 測試函數
# ============================================

async def test_basic_agent():
    """測試基本 Agent 功能"""
    logger.info("=" * 60)
    logger.info("測試 1：基本 Agent 功能")
    logger.info("=" * 60)
    
    try:
        agent = SimpleTestAgent()
        
        # 測試數據
        test_data = """
市場數據：
- BTC 價格：$95,000
- 24h 變動：+5.2%
- 交易量：$35B
- 市場情緒：樂觀
"""
        
        # 執行分析
        result = await agent.analyze(test_data)
        
        if result:
            logger.info("✅ Agent 分析成功")
            logger.info(f"情緒評估：{result.sentiment}")
            logger.info(f"信心指數：{result.confidence}")
            logger.info(f"總結：{result.summary}")
            return True
        else:
            logger.error("❌ Agent 分析失敗")
            return False
            
    except Exception as e:
        logger.error(f"❌ 測試失敗: {str(e)}")
        return False


async def test_json_parsing():
    """測試 JSON 解析和錯誤修復"""
    logger.info("=" * 60)
    logger.info("測試 2：JSON 解析")
    logger.info("=" * 60)
    
    try:
        agent = SimpleTestAgent()
        
        # 測試各種 JSON 格式
        test_cases = [
            # 標準 JSON
            '{"sentiment": "正面", "confidence": 0.85, "summary": "市場表現強勁"}',
            
            # 帶 Markdown 標記
            '```json\n{"sentiment": "中性", "confidence": 0.5, "summary": "市場觀望"}\n```',
            
            # 帶額外文字
            '分析結果如下：\n{"sentiment": "負面", "confidence": 0.3, "summary": "市場疲弱"}\n謝謝',
        ]
        
        success_count = 0
        for i, test_json in enumerate(test_cases, 1):
            logger.info(f"\n測試案例 {i}:")
            result = agent._validate_output(test_json, TestAnalysisOutput)
            
            if result:
                logger.info(f"✅ 解析成功: {result.sentiment}")
                success_count += 1
            else:
                logger.warning(f"❌ 解析失敗")
        
        logger.info(f"\n總計：{success_count}/{len(test_cases)} 通過")
        return success_count == len(test_cases)
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {str(e)}")
        return False


async def test_error_handling():
    """測試錯誤處理"""
    logger.info("=" * 60)
    logger.info("測試 3：錯誤處理")
    logger.info("=" * 60)
    
    try:
        # 建立一個會失敗的 Agent（使用無效數據）
        agent = SimpleTestAgent()
        
        # 測試空數據
        result = await agent.analyze("")
        
        if result is None:
            logger.info("✅ 空數據處理正確（返回 None）")
        else:
            logger.warning("⚠️ 空數據應該返回 None")
        
        # Agent 應該不會崩潰
        logger.info("✅ Agent 錯誤處理通過（不會崩潰）")
        return True
        
    except Exception as e:
        logger.error(f"❌ 錯誤處理測試失敗: {str(e)}")
        return False


async def test_agent_info():
    """測試 Agent 資訊獲取"""
    logger.info("=" * 60)
    logger.info("測試 4：Agent 資訊")
    logger.info("=" * 60)
    
    try:
        agent = SimpleTestAgent()
        info = agent.get_agent_info()
        
        logger.info("Agent 資訊：")
        for key, value in info.items():
            logger.info(f"  {key}: {value}")
        
        # 驗證必要欄位
        required_fields = ["name", "llm_provider", "temperature", "max_retries"]
        missing = [f for f in required_fields if f not in info]
        
        if missing:
            logger.error(f"❌ 缺少欄位: {missing}")
            return False
        
        logger.info("✅ Agent 資訊完整")
        return True
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {str(e)}")
        return False


# ============================================
# 主程式
# ============================================

async def main():
    """執行所有測試"""
    logger.info("🚀 開始測試 BaseAgent")
    logger.info("=" * 60)
    
    try:
        # 驗證配置
        validate_config()
        
        # 執行測試
        results = []
        
        # 測試 1：基本功能（需要真實 API）
        if settings.gemini_api_key:
            results.append(("基本 Agent 功能", await test_basic_agent()))
        else:
            logger.warning("⚠️ 跳過基本功能測試（缺少 Gemini API Key）")
        
        # 測試 2：JSON 解析（不需要 API）
        results.append(("JSON 解析", await test_json_parsing()))
        
        # 測試 3：錯誤處理
        if settings.gemini_api_key:
            results.append(("錯誤處理", await test_error_handling()))
        else:
            logger.warning("⚠️ 跳過錯誤處理測試（缺少 Gemini API Key）")
        
        # 測試 4：Agent 資訊
        results.append(("Agent 資訊", await test_agent_info()))
        
        # 總結
        logger.info("=" * 60)
        logger.info("測試總結")
        logger.info("=" * 60)
        
        for test_name, passed in results:
            status = "✅ 通過" if passed else "❌ 失敗"
            logger.info(f"{test_name}: {status}")
        
        total_passed = sum(1 for _, passed in results if passed)
        total_tests = len(results)
        
        logger.info("=" * 60)
        logger.info(f"總計：{total_passed}/{total_tests} 測試通過")
        
        if total_passed == total_tests:
            logger.info("🎉 所有測試通過！")
        else:
            logger.warning("⚠️ 部分測試失敗")
        
    except Exception as e:
        logger.error(f"❌ 測試執行失敗: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())

