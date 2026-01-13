"""
Editor Agent 快速驗證腳本

測試 Editor Agent 的基本功能：
1. Agent 初始化
2. 衝突偵測邏輯
3. 信心指數計算
4. 完整分析流程（使用模擬數據）
5. 錯誤報告生成

執行方式：
    python -m test_scripts.verify_editor_agent
"""

import asyncio
import sys
import os
from pathlib import Path

# 設定 Windows UTF-8 編碼
if sys.platform == "win32":
    os.environ["PYTHONUTF8"] = "1"
    # 設定標準輸出編碼
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings, validate_config
from src.utils.logger import setup_logger

# 設定日誌
logger = setup_logger(
    name="VerifyEditorAgent",
    log_level="DEBUG",
    console_output=True
)


def create_mock_fed_analysis():
    """建立模擬的 Fed 分析結果"""
    from src.schema.models import FedAnalysisOutput
    
    return FedAnalysisOutput(
        tone_index=-0.2,  # 偏鴿
        key_risks=[
            "市場預期降息過於樂觀",
            "通膨可能出現黏性",
            "就業市場可能開始放緩"
        ],
        summary="當前美債 2Y-10Y 利差收窄，市場正在定價 Fed 在未來幾個季度內轉向寬鬆。然而，Fed 官員的言論仍偏向謹慎，強調通膨目標尚未達成。",
        confidence=0.75,
        yield_curve_status="正常",
        next_fomc_probability=0.35
    )


def create_mock_economic_analysis():
    """建立模擬的經濟分析結果"""
    from src.schema.models import EconomicAnalysisOutput
    
    return EconomicAnalysisOutput(
        soft_landing_score=7.2,  # 偏向軟著陸
        inflation_trend="下降",
        employment_status="強勁",
        key_indicators={
            "CPI_YoY": 3.1,
            "unemployment_rate": 3.8,
            "NFP": 185000,
            "ISM_PMI": 48.5
        },
        summary="經濟數據顯示通膨持續降溫，就業市場保持韌性。ISM PMI 低於 50 顯示製造業收縮，但服務業仍然強勁，整體支持軟著陸預期。",
        confidence=0.80
    )


def create_mock_prediction_analysis():
    """建立模擬的預測市場分析結果"""
    from src.schema.models import PredictionAnalysisOutput
    
    return PredictionAnalysisOutput(
        market_anxiety_score=0.15,  # 輕微焦慮
        key_events=[
            {
                "market": "Fed 三月降息機率",
                "probability": 0.42,
                "change_7d": 0.08,
                "volume": 250000
            },
            {
                "market": "2024 年底前衰退機率",
                "probability": 0.28,
                "change_7d": -0.05,
                "volume": 180000
            }
        ],
        surprising_markets=[
            "Fed 三月降息機率在一週內上升 8%",
            "衰退機率下降至 28%，創近期新低",
            "科技股 ETF 多頭合約交易量激增"
        ],
        summary="預測市場顯示投資者對 Fed 降息預期升溫，但衰退擔憂有所緩解。科技股相關市場活躍度提升，顯示風險偏好改善。",
        confidence=0.70
    )


def create_mock_correlation_analysis():
    """建立模擬的資產連動分析結果"""
    from src.schema.models import CorrelationAnalysisOutput
    
    return CorrelationAnalysisOutput(
        correlation_matrix={
            "BTC-DXY": -0.72,
            "BTC-QQQ": 0.68,
            "SPY-QQQ": 0.94,
            "ETH-BTC": 0.91,
            "GLD-DXY": -0.45
        },
        risk_warnings=[
            "BTC 與納斯達克正相關性強（0.68），風險資產同步性增加",
            "美元指數強勢可能壓制 Crypto 反彈",
            "黃金與美元呈中度負相關，美元走強時黃金承壓"
        ],
        portfolio_impact={
            "BTC-USD": "美元走強可能帶來下行壓力",
            "ETH-USD": "與 BTC 高度連動，波動風險相似",
            "SPY": "與整體市場高度同步"
        },
        summary="當前 BTC 與 DXY 呈現強負相關，美元走勢是影響 Crypto 的關鍵因素。BTC 與納斯達克高度同步，顯示其風險資產屬性增強。",
        confidence=0.82
    )


async def test_agent_initialization():
    """測試 1：Agent 初始化"""
    print("\n" + "=" * 50)
    print("測試 1：Agent 初始化")
    print("=" * 50)
    
    from src.agents.editor_agent import EditorAgent
    
    try:
        agent = EditorAgent()
        print(f"✅ Agent 名稱: {agent.name}")
        print(f"✅ LLM 提供商: {agent.llm_provider}")
        print(f"✅ 溫度設定: {agent.temperature}")
        print(f"✅ 最大重試次數: {agent.max_retries}")
        
        # 測試 System Prompt
        system_prompt = agent.get_system_prompt()
        print(f"✅ System Prompt 長度: {len(system_prompt)} 字元")
        
        return True
    except Exception as e:
        print(f"❌ 初始化失敗: {str(e)}")
        return False


async def test_conflict_detection():
    """測試 2：衝突偵測邏輯"""
    print("\n" + "=" * 50)
    print("測試 2：衝突偵測邏輯")
    print("=" * 50)
    
    from src.agents.editor_agent import EditorAgent
    from src.schema.models import (
        FedAnalysisOutput,
        EconomicAnalysisOutput,
        PredictionAnalysisOutput
    )
    
    agent = EditorAgent()
    
    # 測試情境 1：Fed 鴿派但經濟強勁
    print("\n情境 1：Fed 鴿派但經濟強勁")
    fed_dovish = FedAnalysisOutput(
        tone_index=-0.5,  # 非常鴿
        key_risks=["測試風險"],
        summary="測試摘要",
        confidence=0.8,
        yield_curve_status="正常"
    )
    econ_strong = EconomicAnalysisOutput(
        soft_landing_score=8.5,  # 非常強勁
        inflation_trend="下降",
        employment_status="強勁",
        key_indicators={"CPI": 3.0},
        summary="經濟強勁",
        confidence=0.8
    )
    
    conflicts = agent._detect_conflicts(fed_dovish, econ_strong, None, None)
    if conflicts:
        print(f"✅ 偵測到衝突: {len(conflicts)} 個")
        for c in conflicts:
            print(f"   - {c[:80]}...")
    else:
        print("⚠️ 未偵測到預期的衝突")
    
    # 測試情境 2：市場焦慮但經濟樂觀
    print("\n情境 2：市場焦慮但經濟樂觀")
    prediction_anxious = PredictionAnalysisOutput(
        market_anxiety_score=0.6,  # 焦慮
        key_events=[],
        surprising_markets=[],
        summary="市場焦慮",
        confidence=0.7
    )
    
    conflicts = agent._detect_conflicts(None, econ_strong, prediction_anxious, None)
    if conflicts:
        print(f"✅ 偵測到衝突: {len(conflicts)} 個")
        for c in conflicts:
            print(f"   - {c[:80]}...")
    else:
        print("⚠️ 未偵測到預期的衝突")
    
    return True


async def test_confidence_calculation():
    """測試 3：信心指數計算"""
    print("\n" + "=" * 50)
    print("測試 3：信心指數計算")
    print("=" * 50)
    
    from src.agents.editor_agent import EditorAgent
    
    agent = EditorAgent()
    
    # 建立模擬數據
    fed = create_mock_fed_analysis()
    econ = create_mock_economic_analysis()
    pred = create_mock_prediction_analysis()
    corr = create_mock_correlation_analysis()
    
    # 計算平均信心指數
    avg_confidence = agent._calculate_average_confidence(fed, econ, pred, corr)
    expected_avg = (0.75 + 0.80 + 0.70 + 0.82) / 4
    
    print(f"Fed Agent 信心指數: {fed.confidence:.2%}")
    print(f"Economic Agent 信心指數: {econ.confidence:.2%}")
    print(f"Prediction Agent 信心指數: {pred.confidence:.2%}")
    print(f"Correlation Agent 信心指數: {corr.confidence:.2%}")
    print(f"\n計算的平均值: {avg_confidence:.2%}")
    print(f"預期平均值: {expected_avg:.2%}")
    
    if abs(avg_confidence - expected_avg) < 0.001:
        print("✅ 信心指數計算正確")
        return True
    else:
        print("❌ 信心指數計算錯誤")
        return False


async def test_error_report_generation():
    """測試 4：錯誤報告生成"""
    print("\n" + "=" * 50)
    print("測試 4：錯誤報告生成")
    print("=" * 50)
    
    from src.agents.editor_agent import EditorAgent
    
    agent = EditorAgent()
    
    # 生成錯誤報告
    error_report = agent._generate_error_report()
    
    print(f"✅ 錯誤報告生成成功")
    print(f"   - TL;DR 長度: {len(error_report.tldr)} 字元")
    print(f"   - 亮點數量: {len(error_report.highlights)}")
    print(f"   - 信心指數: {error_report.confidence_score:.2%}")
    print(f"   - Agent 狀態:")
    
    for agent_name, status in error_report.agent_reports.items():
        print(f"     - {agent_name}: {status.get('status', 'unknown')}")
    
    return True


async def test_full_analysis_with_mock_data():
    """測試 5：完整分析流程（使用模擬數據）"""
    print("\n" + "=" * 50)
    print("測試 5：完整分析流程（使用模擬數據）")
    print("=" * 50)
    
    from src.agents.editor_agent import EditorAgent
    
    # 驗證 API 金鑰
    if not settings.gemini_api_key:
        print("⚠️ 未設定 GEMINI_API_KEY，跳過 LLM 測試")
        return True
    
    agent = EditorAgent()
    
    # 準備輸入數據
    input_data = {
        "fed_analysis": create_mock_fed_analysis(),
        "economic_analysis": create_mock_economic_analysis(),
        "prediction_analysis": create_mock_prediction_analysis(),
        "correlation_analysis": create_mock_correlation_analysis()
    }
    
    print("開始執行 Editor Agent 分析...")
    print("（這可能需要 10-30 秒）")
    
    try:
        result = await agent.analyze(input_data)
        
        if result:
            print("\n✅ 分析完成！")
            print(f"\n📋 TL;DR:\n{result.tldr}")
            print(f"\n✨ 深度亮點 ({len(result.highlights)} 個):")
            for i, h in enumerate(result.highlights, 1):
                print(f"   {i}. {h[:100]}...")
            print(f"\n⚠️ 衝突偵測 ({len(result.conflicts)} 個):")
            for c in result.conflicts:
                print(f"   - {c[:100]}...")
            print(f"\n📊 整體信心指數: {result.confidence_score:.0%}")
            print(f"\n💡 投資建議（前 200 字）:")
            print(f"   {result.investment_advice[:200]}...")
            return True
        else:
            print("❌ 分析返回空結果")
            return False
            
    except Exception as e:
        print(f"❌ 分析失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_partial_data_handling():
    """測試 6：部分數據處理（部分 Agent 失敗的情況）"""
    print("\n" + "=" * 50)
    print("測試 6：部分數據處理")
    print("=" * 50)
    
    from src.agents.editor_agent import EditorAgent
    
    agent = EditorAgent()
    
    # 只提供部分數據
    partial_input = {
        "fed_analysis": create_mock_fed_analysis(),
        "economic_analysis": None,  # 模擬失敗
        "prediction_analysis": create_mock_prediction_analysis(),
        "correlation_analysis": None  # 模擬失敗
    }
    
    # 檢查 User Prompt 格式化
    prompt = agent.format_user_prompt(partial_input)
    
    print(f"✅ User Prompt 生成成功（{len(prompt)} 字元）")
    print(f"   包含 '暫時無法取得': {'暫時無法取得' in prompt}")
    
    # 如果有 API 金鑰，執行實際分析
    if settings.gemini_api_key:
        print("\n執行部分數據分析...")
        try:
            result = await agent.analyze(partial_input)
            if result:
                print(f"✅ 部分數據分析成功")
                print(f"   - 信心指數: {result.confidence_score:.0%}")
                print(f"   - 亮點數: {len(result.highlights)}")
                return True
            else:
                print("❌ 分析返回空結果")
                return False
        except Exception as e:
            print(f"⚠️ 分析過程出錯: {str(e)}")
            return False
    else:
        print("⚠️ 未設定 API 金鑰，跳過 LLM 測試")
        return True


async def main():
    """主測試函數"""
    print("=" * 60)
    print("Editor Agent 驗證測試")
    print("=" * 60)
    
    # 驗證配置
    try:
        validate_config()
        print("✅ 配置驗證通過")
    except Exception as e:
        print(f"⚠️ 配置問題: {str(e)}")
    
    results = {}
    
    # 執行測試
    results["初始化"] = await test_agent_initialization()
    results["衝突偵測"] = await test_conflict_detection()
    results["信心指數計算"] = await test_confidence_calculation()
    results["錯誤報告生成"] = await test_error_report_generation()
    results["完整分析"] = await test_full_analysis_with_mock_data()
    results["部分數據處理"] = await test_partial_data_handling()
    
    # 輸出結果總結
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {test_name}")
    
    print(f"\n總計：{passed}/{total} 測試通過")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
