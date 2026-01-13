"""
MacroPulse - AI 總經與預測市場分析系統
主程式入口點

本系統採用多 Agent 協同模式，自動化分析：
- 聯準會貨幣政策
- 經濟指標趨勢
- 預測市場情緒
- 資產連動性

參考文件：README_Main_System.md, AGENT.md
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 配置管理
from config import settings, validate_config

# 日誌系統
from src.utils.logger import setup_logger
from src.utils.formatters import format_date

# 全域 logger
logger = setup_logger(
    name="MacroPulse",
    log_level=settings.log_level,
    log_file=None,  # 暫時不輸出到檔案
    console_output=True
)


async def collect_data():
    """
    數據採集階段
    
    從各個 API 採集原始數據：
    - Polymarket 預測市場數據
    - FRED 經濟指標數據
    - yfinance 市場數據
    
    Returns:
        dict: 採集的數據
    """
    logger.info("=" * 60)
    logger.info("階段 1：數據採集")
    logger.info("=" * 60)
    
    from src.collectors.polymarket_data import PolymarketCollector
    from src.collectors.fred_data import FREDCollector
    from src.collectors.market_data import MarketDataCollector
    
    # 建立採集器
    polymarket_collector = PolymarketCollector()
    fred_collector = FREDCollector()
    market_collector = MarketDataCollector()
    
    # 並行採集數據
    try:
        logger.info("開始並行採集數據...")
        
        # 使用 asyncio.gather 並行執行
        polymarket_task = polymarket_collector.collect(limit=20)
        fred_task = fred_collector.collect()
        treasury_task = market_collector.collect_treasury_yields()
        asset_task = market_collector.collect_asset_prices(days=7)
        
        polymarket_data, fred_data, treasury_yields, asset_prices = await asyncio.gather(
            polymarket_task,
            fred_task,
            treasury_task,
            asset_task,
            return_exceptions=True
        )
        
        # 檢查錯誤
        if isinstance(polymarket_data, Exception):
            logger.error(f"Polymarket 採集失敗：{str(polymarket_data)}")
            polymarket_data = []
        
        if isinstance(fred_data, Exception):
            logger.error(f"FRED 採集失敗：{str(fred_data)}")
            fred_data = {}
        
        if isinstance(treasury_yields, Exception):
            logger.error(f"美債殖利率採集失敗：{str(treasury_yields)}")
            treasury_yields = []
        
        if isinstance(asset_prices, Exception):
            logger.error(f"資產價格採集失敗：{str(asset_prices)}")
            asset_prices = {}
        
        # 記錄採集結果
        logger.info(f"✅ Polymarket 市場：{len(polymarket_data)} 個")
        logger.info(f"✅ FRED 經濟指標：{len(fred_data)} 個系列")
        logger.info(f"✅ 美債殖利率：{len(treasury_yields)} 個")
        logger.info(f"✅ 資產價格歷史：{len(asset_prices)} 個")
        
        return {
            'polymarket': polymarket_data,
            'fred': fred_data,
            'treasury_yields': treasury_yields,
            'asset_prices': asset_prices
        }
        
    except Exception as e:
        logger.error(f"數據採集失敗：{str(e)}", exc_info=True)
        return {
            'polymarket': [],
            'fred': {},
            'treasury_yields': [],
            'asset_prices': {}
        }


async def run_analysis(data: dict):
    """
    分析階段
    
    運行所有專業 Agent 進行分析：
    - FedAgent: 貨幣政策分析
    - EconAgent: 經濟指標分析
    - SentimentAgent: 預測市場分析
    - CorrelationAgent: 資產連動分析
    
    實作優雅降級：單一 Agent 失敗不會中斷整體流程。
    
    Args:
        data: 採集的數據，包含：
            - polymarket: List[PolymarketMarket]
            - fred: Dict[str, FREDSeries]
            - treasury_yields: List[TreasuryYield]
            - asset_prices: Dict[str, AssetPriceHistory]
        
    Returns:
        dict: 各 Agent 的分析結果
    """
    logger.info("=" * 60)
    logger.info("階段 2：專業分析")
    logger.info("=" * 60)
    
    # 導入所有 Agent
    from src.agents import FedAgent, EconAgent, SentimentAgent, CorrelationAgent
    
    # 初始化結果字典
    results = {
        'fed_analysis': None,
        'economic_analysis': None,
        'prediction_analysis': None,
        'correlation_analysis': None
    }
    
    # 解構數據
    polymarket_data = data.get('polymarket', [])
    fred_data = data.get('fred', {})
    treasury_yields = data.get('treasury_yields', [])
    asset_prices = data.get('asset_prices', {})
    
    # 獲取用戶持倉配置（可選）
    user_portfolio = None
    portfolio_list = settings.get_user_portfolio_list()
    if portfolio_list:
        from src.schema.models import UserPortfolio
        user_portfolio = UserPortfolio(holdings=portfolio_list)
        logger.info(f"已載入用戶持倉：{len(portfolio_list)} 個標的")
    
    # 檢查數據可用性
    data_status = {
        'treasury_yields': len(treasury_yields) > 0,
        'fred_data': len(fred_data) > 0,
        'polymarket': len(polymarket_data) > 0,
        'asset_prices': len(asset_prices) > 0
    }
    logger.info(f"數據可用性：{data_status}")
    
    # 建立 Agent 實例
    fed_agent = FedAgent()
    econ_agent = EconAgent()
    sentiment_agent = SentimentAgent()
    correlation_agent = CorrelationAgent()
    
    # 準備各 Agent 的輸入數據
    fed_input = {
        "treasury_yields": treasury_yields,
        "polymarket_data": polymarket_data  # 可選：Fed 相關的預測市場
    }
    
    econ_input = {
        "fred_data": fred_data
    }
    
    sentiment_input = {
        "polymarket_data": polymarket_data
    }
    
    correlation_input = {
        "asset_prices": asset_prices,
        "user_portfolio": user_portfolio
    }
    
    # 定義單一 Agent 執行包裝器（用於優雅降級）
    async def safe_analyze(agent, input_data, agent_name: str):
        """
        安全執行 Agent 分析，捕獲並記錄異常
        
        Args:
            agent: Agent 實例
            input_data: 輸入數據
            agent_name: Agent 名稱（用於日誌）
            
        Returns:
            分析結果或 None（失敗時）
        """
        try:
            logger.info(f"開始執行 {agent_name}...")
            result = await agent.analyze(input_data)
            if result:
                logger.info(f"{agent_name} 分析成功")
            else:
                logger.warning(f"{agent_name} 返回空結果（可能數據不足）")
            return result
        except Exception as e:
            logger.error(f"{agent_name} 執行失敗：{str(e)}", exc_info=True)
            return None
    
    # 並行執行所有 Agent（使用 asyncio.gather）
    logger.info("開始並行執行所有分析 Agent...")
    
    fed_task = safe_analyze(fed_agent, fed_input, "FedAgent")
    econ_task = safe_analyze(econ_agent, econ_input, "EconAgent")
    sentiment_task = safe_analyze(sentiment_agent, sentiment_input, "SentimentAgent")
    correlation_task = safe_analyze(correlation_agent, correlation_input, "CorrelationAgent")
    
    # 等待所有任務完成
    analysis_results = await asyncio.gather(
        fed_task,
        econ_task,
        sentiment_task,
        correlation_task,
        return_exceptions=True  # 確保異常不會中斷其他任務
    )
    
    # 處理結果
    agent_names = ['fed_analysis', 'economic_analysis', 'prediction_analysis', 'correlation_analysis']
    display_names = ['FedAgent', 'EconAgent', 'SentimentAgent', 'CorrelationAgent']
    
    success_count = 0
    for i, (name, result) in enumerate(zip(agent_names, analysis_results)):
        if isinstance(result, Exception):
            # asyncio.gather 捕獲的異常（理論上不會到這裡，因為 safe_analyze 已處理）
            logger.error(f"{display_names[i]} 發生未預期異常：{str(result)}")
            results[name] = None
        else:
            results[name] = result
            if result is not None:
                success_count += 1
    
    # 輸出總結
    logger.info("-" * 40)
    logger.info(f"分析完成：{success_count}/{len(agent_names)} 個 Agent 成功")
    
    if success_count == 0:
        logger.warning("所有 Agent 分析均失敗，請檢查 API 配置和數據來源")
    elif success_count < len(agent_names):
        failed_agents = [
            display_names[i] for i, name in enumerate(agent_names) 
            if results[name] is None
        ]
        logger.warning(f"部分 Agent 失敗：{', '.join(failed_agents)}")
    
    return results


async def generate_report(analysis_results: dict):
    """
    報告生成階段
    
    由 Editor Agent 整合所有分析結果，生成最終報告。
    
    Args:
        analysis_results: 各 Agent 的分析結果
        
    Returns:
        str: 報告檔案路徑
    """
    logger.info("=" * 60)
    logger.info("階段 3：報告生成（Editor Agent）")
    logger.info("=" * 60)
    
    from src.agents.editor_agent import EditorAgent
    
    # 生成報告檔案名稱
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"report_{timestamp}.md"
    report_path = settings.output_dir / report_filename
    
    # 解構分析結果
    fed_analysis = analysis_results.get('fed_analysis')
    economic_analysis = analysis_results.get('economic_analysis')
    prediction_analysis = analysis_results.get('prediction_analysis')
    correlation_analysis = analysis_results.get('correlation_analysis')
    
    # 統計成功的分析
    success_count = sum(1 for v in analysis_results.values() if v is not None)
    total_count = len(analysis_results)
    
    logger.info(f"可用分析報告：{success_count}/{total_count}")
    
    # 初始化 Editor Agent
    editor_agent = EditorAgent()
    
    # 準備 Editor Agent 輸入
    editor_input = {
        "fed_analysis": fed_analysis,
        "economic_analysis": economic_analysis,
        "prediction_analysis": prediction_analysis,
        "correlation_analysis": correlation_analysis
    }
    
    # 執行 Editor Agent 分析
    try:
        final_report = await editor_agent.analyze(editor_input)
        
        if final_report:
            # 生成 Markdown 報告
            report_content = _format_final_report_to_markdown(
                final_report, 
                fed_analysis, 
                economic_analysis, 
                prediction_analysis, 
                correlation_analysis
            )
        else:
            logger.warning("Editor Agent 返回空結果，使用備用報告格式")
            report_content = _generate_fallback_report(
                fed_analysis, 
                economic_analysis, 
                prediction_analysis, 
                correlation_analysis
            )
            
    except Exception as e:
        logger.error(f"Editor Agent 執行失敗：{str(e)}", exc_info=True)
        logger.info("使用備用報告格式")
        report_content = _generate_fallback_report(
            fed_analysis, 
            economic_analysis, 
            prediction_analysis, 
            correlation_analysis
        )
    
    # 寫入報告
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"報告已生成：{report_path}")
    
    return str(report_path)


def _format_final_report_to_markdown(
    final_report,
    fed_analysis,
    economic_analysis,
    prediction_analysis,
    correlation_analysis
) -> str:
    """
    將 FinalReport 模型格式化為 Markdown 報告
    
    Args:
        final_report: Editor Agent 生成的 FinalReport
        fed_analysis: 貨幣政策分析結果
        economic_analysis: 經濟指標分析結果
        prediction_analysis: 預測市場分析結果
        correlation_analysis: 資產連動分析結果
    
    Returns:
        str: Markdown 格式的報告內容
    """
    report_content = f"""# MacroPulse 總經分析報告

**生成時間**: {format_date(final_report.timestamp, 'long')}  
**報告版本**: v0.4.0  
**整體信心指數**: {final_report.confidence_score:.0%}

---

## 📋 TL;DR（三句話總結）

{final_report.tldr}

---

## ✨ 深度亮點

"""
    
    # 亮點列表
    for i, highlight in enumerate(final_report.highlights, 1):
        report_content += f"{i}. **{highlight}**\n"
    
    report_content += "\n---\n\n"
    
    # 邏輯衝突（如果存在）
    if final_report.conflicts:
        report_content += "## ⚠️ 邏輯衝突與風險提示\n\n"
        for conflict in final_report.conflicts:
            report_content += f"- {conflict}\n"
        report_content += "\n---\n\n"
    
    # 投資建議
    report_content += f"""## 💡 投資建議

{final_report.investment_advice}

---

## 📊 詳細分析報告

"""
    
    # === 貨幣政策分析 ===
    report_content += "### 🏦 貨幣政策分析 (Fed Watcher)\n\n"
    if fed_analysis:
        report_content += f"- **鷹/鴿指數**: {fed_analysis.tone_index:.2f} (-1.0 極鴿 ~ 1.0 極鷹)\n"
        report_content += f"- **殖利率曲線狀態**: {fed_analysis.yield_curve_status}\n"
        report_content += f"- **信心指數**: {fed_analysis.confidence:.0%}\n"
        report_content += f"\n**摘要**: {fed_analysis.summary}\n\n"
        if fed_analysis.key_risks:
            report_content += "**關鍵風險**:\n"
            for risk in fed_analysis.key_risks[:3]:
                report_content += f"- {risk}\n"
    else:
        report_content += "_分析未完成（數據不足或 API 錯誤）_\n"
    report_content += "\n---\n\n"
    
    # === 經濟指標分析 ===
    report_content += "### 📈 經濟指標分析 (Data Analyst)\n\n"
    if economic_analysis:
        report_content += f"- **軟著陸評分**: {economic_analysis.soft_landing_score:.1f}/10\n"
        report_content += f"- **通膨趨勢**: {economic_analysis.inflation_trend}\n"
        report_content += f"- **就業狀況**: {economic_analysis.employment_status}\n"
        report_content += f"- **信心指數**: {economic_analysis.confidence:.0%}\n"
        report_content += f"\n**摘要**: {economic_analysis.summary}\n"
    else:
        report_content += "_分析未完成（數據不足或 API 錯誤）_\n"
    report_content += "\n---\n\n"
    
    # === 預測市場分析 ===
    report_content += "### 🔮 預測市場分析 (Prediction Specialist)\n\n"
    if prediction_analysis:
        anxiety_desc = "焦慮" if prediction_analysis.market_anxiety_score > 0.2 else \
                       "樂觀" if prediction_analysis.market_anxiety_score < -0.2 else "中性"
        report_content += f"- **市場情緒**: {anxiety_desc} (指數: {prediction_analysis.market_anxiety_score:.2f})\n"
        report_content += f"- **信心指數**: {prediction_analysis.confidence:.0%}\n"
        report_content += f"\n**摘要**: {prediction_analysis.summary}\n\n"
        if prediction_analysis.surprising_markets:
            report_content += "**值得關注的市場**:\n"
            for market in prediction_analysis.surprising_markets[:3]:
                report_content += f"- {market}\n"
    else:
        report_content += "_分析未完成（數據不足或 API 錯誤）_\n"
    report_content += "\n---\n\n"
    
    # === 資產連動分析 ===
    report_content += "### 🔗 資產連動分析 (Correlation Expert)\n\n"
    if correlation_analysis:
        report_content += f"- **信心指數**: {correlation_analysis.confidence:.0%}\n"
        report_content += f"\n**摘要**: {correlation_analysis.summary}\n\n"
        if correlation_analysis.correlation_matrix:
            report_content += "**相關係數矩陣**:\n"
            report_content += "| 資產配對 | 相關係數 |\n"
            report_content += "|---------|----------|\n"
            for pair, corr in list(correlation_analysis.correlation_matrix.items())[:5]:
                report_content += f"| {pair} | {corr:.2f} |\n"
            report_content += "\n"
        if correlation_analysis.risk_warnings:
            report_content += "**風險預警**:\n"
            for warning in correlation_analysis.risk_warnings[:3]:
                report_content += f"- {warning}\n"
    else:
        report_content += "_分析未完成（數據不足或 API 錯誤）_\n"
    report_content += "\n---\n\n"
    
    # === 免責聲明 ===
    report_content += """## ⚠️ 免責聲明

本報告由 AI 自動生成，僅供參考，不構成投資建議。投資有風險，決策需謹慎。

---

**MacroPulse** - AI 總經與預測市場分析系統  
**系統狀態**: Phase 4 完成（Editor Agent 整合完成）
"""
    
    return report_content


def _generate_fallback_report(
    fed_analysis,
    economic_analysis,
    prediction_analysis,
    correlation_analysis
) -> str:
    """
    生成備用報告（當 Editor Agent 失敗時使用）
    
    Args:
        fed_analysis: 貨幣政策分析結果
        economic_analysis: 經濟指標分析結果
        prediction_analysis: 預測市場分析結果
        correlation_analysis: 資產連動分析結果
    
    Returns:
        str: Markdown 格式的備用報告
    """
    # 統計成功的分析
    analyses = [fed_analysis, economic_analysis, prediction_analysis, correlation_analysis]
    success_count = sum(1 for v in analyses if v is not None)
    total_count = len(analyses)
    
    report_content = f"""# MacroPulse 總經分析報告（備用格式）

**生成時間**: {format_date(datetime.now(), 'long')}  
**報告版本**: v0.4.0  
**報告類型**: 備用格式（Editor Agent 整合失敗）

---

## 📊 分析摘要

分析完成度：{success_count}/{total_count} 個 Agent 成功

"""

    # === 貨幣政策分析 ===
    report_content += "### 🏦 貨幣政策分析 (Fed Watcher)\n\n"
    if fed_analysis:
        report_content += f"- **鷹/鴿指數**: {fed_analysis.tone_index:.2f} (-1.0 極鴿 ~ 1.0 極鷹)\n"
        report_content += f"- **殖利率曲線狀態**: {fed_analysis.yield_curve_status}\n"
        report_content += f"- **信心指數**: {fed_analysis.confidence:.0%}\n"
        report_content += f"\n**摘要**: {fed_analysis.summary}\n\n"
        if fed_analysis.key_risks:
            report_content += "**關鍵風險**:\n"
            for risk in fed_analysis.key_risks[:3]:
                report_content += f"- {risk}\n"
    else:
        report_content += "_分析未完成（數據不足或 API 錯誤）_\n"
    report_content += "\n---\n\n"
    
    # === 經濟指標分析 ===
    report_content += "### 📈 經濟指標分析 (Data Analyst)\n\n"
    if economic_analysis:
        report_content += f"- **軟著陸評分**: {economic_analysis.soft_landing_score:.1f}/10\n"
        report_content += f"- **通膨趨勢**: {economic_analysis.inflation_trend}\n"
        report_content += f"- **就業狀況**: {economic_analysis.employment_status}\n"
        report_content += f"- **信心指數**: {economic_analysis.confidence:.0%}\n"
        report_content += f"\n**摘要**: {economic_analysis.summary}\n"
    else:
        report_content += "_分析未完成（數據不足或 API 錯誤）_\n"
    report_content += "\n---\n\n"
    
    # === 預測市場分析 ===
    report_content += "### 🔮 預測市場分析 (Prediction Specialist)\n\n"
    if prediction_analysis:
        anxiety_desc = "焦慮" if prediction_analysis.market_anxiety_score > 0.2 else \
                       "樂觀" if prediction_analysis.market_anxiety_score < -0.2 else "中性"
        report_content += f"- **市場情緒**: {anxiety_desc} (指數: {prediction_analysis.market_anxiety_score:.2f})\n"
        report_content += f"- **信心指數**: {prediction_analysis.confidence:.0%}\n"
        report_content += f"\n**摘要**: {prediction_analysis.summary}\n\n"
        if prediction_analysis.surprising_markets:
            report_content += "**值得關注的市場**:\n"
            for market in prediction_analysis.surprising_markets[:3]:
                report_content += f"- {market}\n"
    else:
        report_content += "_分析未完成（數據不足或 API 錯誤）_\n"
    report_content += "\n---\n\n"
    
    # === 資產連動分析 ===
    report_content += "### 🔗 資產連動分析 (Correlation Expert)\n\n"
    if correlation_analysis:
        report_content += f"- **信心指數**: {correlation_analysis.confidence:.0%}\n"
        report_content += f"\n**摘要**: {correlation_analysis.summary}\n\n"
        if correlation_analysis.correlation_matrix:
            report_content += "**相關係數矩陣**:\n"
            report_content += "| 資產配對 | 相關係數 |\n"
            report_content += "|---------|----------|\n"
            for pair, corr in list(correlation_analysis.correlation_matrix.items())[:5]:
                report_content += f"| {pair} | {corr:.2f} |\n"
            report_content += "\n"
        if correlation_analysis.risk_warnings:
            report_content += "**風險預警**:\n"
            for warning in correlation_analysis.risk_warnings[:3]:
                report_content += f"- {warning}\n"
    else:
        report_content += "_分析未完成（數據不足或 API 錯誤）_\n"
    report_content += "\n---\n\n"
    
    # === 免責聲明 ===
    report_content += """## ⚠️ 免責聲明

本報告由 AI 自動生成，僅供參考，不構成投資建議。投資有風險，決策需謹慎。

---

**MacroPulse** - AI 總經與預測市場分析系統  
**系統狀態**: Phase 4（備用報告模式）
"""
    
    return report_content


async def main():
    """
    主程式入口
    
    執行流程：
    1. 驗證配置
    2. 數據採集
    3. 專業分析
    4. 報告生成
    """
    try:
        # 顯示啟動資訊
        logger.info("=" * 60)
        logger.info("MacroPulse - AI 總經與預測市場分析系統")
        logger.info("版本：v0.4.0")
        logger.info("=" * 60)
        
        # 驗證配置
        logger.info("驗證配置...")
        validate_config()
        
        # 階段 1：數據採集
        data = await collect_data()
        
        # 階段 2：專業分析
        analysis_results = await run_analysis(data)
        
        # 階段 3：報告生成
        report_path = await generate_report(analysis_results)
        
        # 完成
        logger.info("=" * 60)
        logger.info("✅ 分析完成！")
        logger.info(f"📄 報告位置：{report_path}")
        logger.info("=" * 60)
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("用戶中斷執行")
        return 130
    except Exception as e:
        logger.error(f"執行失敗：{str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    # 設定 Windows 環境的 UTF-8 編碼
    if sys.platform == "win32":
        import os
        os.environ["PYTHONUTF8"] = "1"
    
    # 執行主程式
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

