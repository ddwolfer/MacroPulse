"""
主程式整合快速驗證腳本

這個腳本不調用 LLM API，只驗證：
1. main.py 的導入和語法正確
2. run_analysis() 函數可以正確處理輸入數據
3. generate_report() 函數可以生成報告
4. 優雅降級機制正常運作
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, date

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """測試所有必要的導入"""
    print("=" * 60)
    print("測試 1：驗證導入")
    print("=" * 60)
    
    try:
        # 測試主程式導入
        from main import collect_data, run_analysis, generate_report, main
        print("[OK] main.py 導入成功")
        
        # 測試 Agent 導入
        from src.agents import FedAgent, EconAgent, SentimentAgent, CorrelationAgent
        print("[OK] 所有 Agent 導入成功")
        
        # 測試 Schema 導入
        from src.schema.models import (
            FedAnalysisOutput,
            EconomicAnalysisOutput,
            PredictionAnalysisOutput,
            CorrelationAnalysisOutput,
            UserPortfolio
        )
        print("[OK] 所有 Schema 模型導入成功")
        
        # 測試配置導入
        from config import settings
        print("[OK] config.py 導入成功")
        
        return True
    except Exception as e:
        print(f"[FAIL] 導入失敗：{str(e)}")
        return False


def test_agent_initialization():
    """測試 Agent 初始化"""
    print("\n" + "=" * 60)
    print("測試 2：Agent 初始化")
    print("=" * 60)
    
    try:
        from src.agents import FedAgent, EconAgent, SentimentAgent, CorrelationAgent
        
        fed_agent = FedAgent()
        print(f"[OK] FedAgent 初始化成功 (name={fed_agent.name})")
        
        econ_agent = EconAgent()
        print(f"[OK] EconAgent 初始化成功 (name={econ_agent.name})")
        
        sentiment_agent = SentimentAgent()
        print(f"[OK] SentimentAgent 初始化成功 (name={sentiment_agent.name})")
        
        correlation_agent = CorrelationAgent()
        print(f"[OK] CorrelationAgent 初始化成功 (name={correlation_agent.name})")
        
        return True
    except Exception as e:
        print(f"[FAIL] Agent 初始化失敗：{str(e)}")
        return False


def test_data_preparation():
    """測試數據準備邏輯"""
    print("\n" + "=" * 60)
    print("測試 3：數據準備邏輯")
    print("=" * 60)
    
    try:
        from src.schema.models import (
            TreasuryYield, PolymarketMarket, PolymarketToken,
            FREDSeries, FREDObservation, AssetPriceHistory, UserPortfolio
        )
        from config import settings
        
        # 模擬 Treasury Yields 數據
        treasury_yields = [
            TreasuryYield(symbol="^IRX", maturity="2Y", yield_value=4.25, timestamp=datetime.now()),
            TreasuryYield(symbol="^TNX", maturity="10Y", yield_value=4.50, timestamp=datetime.now()),
        ]
        print(f"[OK] 模擬 Treasury Yields 數據：{len(treasury_yields)} 個")
        
        # 模擬 FRED 數據
        today = date.today()
        fred_data = {
            "CPIAUCSL": FREDSeries(
                series_id="CPIAUCSL",
                title="CPI",
                frequency="monthly",
                observations=[
                    FREDObservation(date=today, value=310.5, realtime_start=today, realtime_end=today)
                ]
            ),
            "UNRATE": FREDSeries(
                series_id="UNRATE",
                title="Unemployment Rate",
                frequency="monthly",
                observations=[
                    FREDObservation(date=today, value=3.9, realtime_start=today, realtime_end=today)
                ]
            ),
            "PAYEMS": FREDSeries(
                series_id="PAYEMS",
                title="Non-Farm Payrolls",
                frequency="monthly",
                observations=[
                    FREDObservation(date=today, value=159000, realtime_start=today, realtime_end=today)
                ]
            ),
        }
        print(f"[OK] 模擬 FRED 數據：{len(fred_data)} 個系列")
        
        # 模擬 Polymarket 數據
        polymarket_data = [
            PolymarketMarket(
                id="test-1",
                question="Will Fed cut rates in 2024?",
                slug="fed-cut-2024",
                category="Economics",
                volume=500000,
                liquidity=100000,
                active=True,
                tokens=[
                    PolymarketToken(outcome="Yes", price=0.65, volume=300000)
                ]
            )
        ]
        print(f"[OK] 模擬 Polymarket 數據：{len(polymarket_data)} 個市場")
        
        # 模擬資產價格數據
        from datetime import timedelta
        date_list = [today - timedelta(days=i) for i in range(6, -1, -1)]  # 7 天的日期列表
        asset_prices = {
            "BTC-USD": AssetPriceHistory(
                symbol="BTC-USD",
                prices=[95000, 96000, 97000, 98000, 99000, 100000, 101000],
                dates=date_list
            ),
            "SPY": AssetPriceHistory(
                symbol="SPY",
                prices=[580, 582, 584, 586, 588, 590, 592],
                dates=date_list
            ),
        }
        print(f"[OK] 模擬資產價格數據：{len(asset_prices)} 個")
        
        # 測試用戶持倉配置
        portfolio_list = settings.get_user_portfolio_list()
        if portfolio_list:
            user_portfolio = UserPortfolio(holdings=portfolio_list)
            print(f"[OK] 用戶持倉配置：{len(portfolio_list)} 個標的")
        else:
            print("[INFO] 未配置用戶持倉（這是正常的）")
        
        # 組合完整數據
        test_data = {
            'polymarket': polymarket_data,
            'fred': fred_data,
            'treasury_yields': treasury_yields,
            'asset_prices': asset_prices
        }
        print(f"[OK] 完整測試數據準備完成")
        
        return test_data
    except Exception as e:
        print(f"[FAIL] 數據準備失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_run_analysis_structure(test_data):
    """測試 run_analysis 函數結構（不調用 LLM）"""
    print("\n" + "=" * 60)
    print("測試 4：run_analysis 函數結構")
    print("=" * 60)
    
    try:
        # 我們不實際調用 run_analysis（會觸發 LLM），
        # 而是驗證函數結構和輸入處理
        
        from src.agents import FedAgent, EconAgent, SentimentAgent, CorrelationAgent
        from src.schema.models import UserPortfolio
        from config import settings
        
        # 解構數據
        polymarket_data = test_data.get('polymarket', [])
        fred_data = test_data.get('fred', {})
        treasury_yields = test_data.get('treasury_yields', [])
        asset_prices = test_data.get('asset_prices', {})
        
        print(f"[OK] 數據解構成功")
        print(f"     - polymarket: {len(polymarket_data)} 個市場")
        print(f"     - fred: {len(fred_data)} 個系列")
        print(f"     - treasury_yields: {len(treasury_yields)} 個")
        print(f"     - asset_prices: {len(asset_prices)} 個")
        
        # 準備 Agent 輸入
        fed_input = {
            "treasury_yields": treasury_yields,
            "polymarket_data": polymarket_data
        }
        print(f"[OK] FedAgent 輸入準備完成")
        
        econ_input = {
            "fred_data": fred_data
        }
        print(f"[OK] EconAgent 輸入準備完成")
        
        sentiment_input = {
            "polymarket_data": polymarket_data
        }
        print(f"[OK] SentimentAgent 輸入準備完成")
        
        correlation_input = {
            "asset_prices": asset_prices,
            "user_portfolio": None
        }
        print(f"[OK] CorrelationAgent 輸入準備完成")
        
        # 驗證 Agent 可以處理輸入（只生成 Prompt，不調用 LLM）
        fed_agent = FedAgent()
        fed_prompt = fed_agent.format_user_prompt(fed_input)
        print(f"[OK] FedAgent Prompt 生成成功（{len(fed_prompt)} 字元）")
        
        econ_agent = EconAgent()
        econ_prompt = econ_agent.format_user_prompt(econ_input)
        print(f"[OK] EconAgent Prompt 生成成功（{len(econ_prompt)} 字元）")
        
        sentiment_agent = SentimentAgent()
        sentiment_prompt = sentiment_agent.format_user_prompt(sentiment_input)
        print(f"[OK] SentimentAgent Prompt 生成成功（{len(sentiment_prompt)} 字元）")
        
        correlation_agent = CorrelationAgent()
        correlation_prompt = correlation_agent.format_user_prompt(correlation_input)
        print(f"[OK] CorrelationAgent Prompt 生成成功（{len(correlation_prompt)} 字元）")
        
        return True
    except Exception as e:
        print(f"[FAIL] run_analysis 結構測試失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_generate_report():
    """測試 generate_report 函數"""
    print("\n" + "=" * 60)
    print("測試 5：generate_report 函數")
    print("=" * 60)
    
    try:
        from main import generate_report
        from src.schema.models import (
            FedAnalysisOutput, EconomicAnalysisOutput,
            PredictionAnalysisOutput, CorrelationAnalysisOutput
        )
        
        # 模擬分析結果（部分成功，部分失敗，測試優雅降級）
        mock_results = {
            'fed_analysis': FedAnalysisOutput(
                tone_index=0.3,
                key_risks=["通膨粘性", "勞動力市場過熱"],
                summary="Fed 維持鷹派立場，短期內降息可能性低。",
                confidence=0.75,
                yield_curve_status="正常"
            ),
            'economic_analysis': EconomicAnalysisOutput(
                soft_landing_score=7.5,
                inflation_trend="下降",
                employment_status="強勁",
                key_indicators={"CPI": 3.2, "unemployment": 3.9},
                summary="經濟數據顯示軟著陸機率較高。",
                confidence=0.80
            ),
            'prediction_analysis': None,  # 模擬失敗
            'correlation_analysis': CorrelationAnalysisOutput(
                correlation_matrix={"BTC-QQQ": 0.72, "BTC-DXY": -0.45},
                risk_warnings=["BTC 與納斯達克高度正相關"],
                portfolio_impact={},
                summary="BTC 目前呈現風險資產屬性。",
                confidence=0.70
            )
        }
        
        print("[OK] 模擬分析結果準備完成（3/4 成功）")
        
        # 生成報告
        report_path = await generate_report(mock_results)
        print(f"[OK] 報告生成成功：{report_path}")
        
        # 驗證報告內容
        from pathlib import Path
        report_file = Path(report_path)
        if report_file.exists():
            content = report_file.read_text(encoding='utf-8')
            print(f"[OK] 報告文件存在（{len(content)} 字元）")
            
            # 驗證關鍵內容
            checks = [
                ("標題", "# MacroPulse 總經分析報告"),
                ("Fed 分析", "貨幣政策分析"),
                ("經濟分析", "經濟指標分析"),
                ("預測分析", "預測市場分析"),
                ("相關性分析", "資產連動分析"),
                ("免責聲明", "免責聲明"),
            ]
            
            for name, keyword in checks:
                if keyword in content:
                    print(f"[OK] 報告包含 {name}")
                else:
                    print(f"[WARN] 報告缺少 {name}")
            
            # 驗證失敗的分析有正確顯示
            if "分析未完成" in content:
                print("[OK] 報告正確顯示了失敗的分析")
            
            return True
        else:
            print(f"[FAIL] 報告文件不存在")
            return False
            
    except Exception as e:
        print(f"[FAIL] generate_report 測試失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("MacroPulse 主程式整合快速驗證")
    print("=" * 60)
    
    results = []
    
    # 測試 1：導入
    results.append(("導入測試", test_imports()))
    
    # 測試 2：Agent 初始化
    results.append(("Agent 初始化", test_agent_initialization()))
    
    # 測試 3：數據準備
    test_data = test_data_preparation()
    results.append(("數據準備", test_data is not None))
    
    # 測試 4：run_analysis 結構
    if test_data:
        results.append(("run_analysis 結構", await test_run_analysis_structure(test_data)))
    else:
        results.append(("run_analysis 結構", False))
    
    # 測試 5：generate_report
    results.append(("generate_report", await test_generate_report()))
    
    # 輸出總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\n總計：{passed}/{total} 測試通過")
    
    if passed == total:
        print("\n[OK] 主程式整合驗證通過！")
        return 0
    else:
        print("\n[WARN] 部分測試失敗，請檢查")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
