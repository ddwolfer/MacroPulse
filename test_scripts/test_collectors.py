"""
測試數據採集器

驗證 Polymarket、FRED、yfinance 採集器是否正常運作。
"""

import sys
import os
import asyncio
from pathlib import Path

# Windows UTF-8 支援
if sys.platform == "win32":
    os.environ["PYTHONUTF8"] = "1"
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger
from src.collectors.polymarket_data import PolymarketCollector
from src.collectors.fred_data import FREDCollector
from src.collectors.market_data import MarketDataCollector

logger = setup_logger(name="TestCollectors", log_level="DEBUG")


async def test_polymarket():
    """測試 Polymarket 採集器"""
    print("\n" + "=" * 60)
    print("測試 1: Polymarket 採集器")
    print("=" * 60)
    
    try:
        collector = PolymarketCollector()
        markets = await collector.collect(limit=5)
        
        print(f"成功採集 {len(markets)} 個市場")
        for i, market in enumerate(markets[:3], 1):
            print(f"\n市場 {i}:")
            print(f"  問題: {market.question}")
            print(f"  交易量: ${market.volume:,.0f}")
            print(f"  代幣: {len(market.tokens)} 個")
            for token in market.tokens:
                print(f"    - {token.outcome}: {token.price:.2%}")
        
        print("\n✅ Polymarket 測試通過")
        return True
    except Exception as e:
        print(f"\n❌ Polymarket 測試失敗: {str(e)}")
        return False


async def test_fred():
    """測試 FRED 採集器"""
    print("\n" + "=" * 60)
    print("測試 2: FRED 採集器")
    print("=" * 60)
    
    try:
        collector = FREDCollector()
        data = await collector.collect(series_ids=["CPIAUCSL", "UNRATE"])
        
        print(f"成功採集 {len(data)} 個系列")
        for series_id, series in data.items():
            latest_value = series.get_latest_value()
            print(f"\n系列: {series.title} ({series_id})")
            print(f"  最新值: {latest_value}")
            print(f"  觀測值數量: {len(series.observations)}")
        
        print("\n✅ FRED 測試通過")
        return True
    except Exception as e:
        print(f"\n❌ FRED 測試失敗: {str(e)}")
        logger.error(f"FRED 測試錯誤詳情", exc_info=True)
        return False


async def test_market_data():
    """測試市場數據採集器"""
    print("\n" + "=" * 60)
    print("測試 3: 市場數據採集器")
    print("=" * 60)
    
    try:
        collector = MarketDataCollector()
        
        # 測試美債殖利率
        yields = await collector.collect_treasury_yields()
        print(f"\n成功採集 {len(yields)} 個美債殖利率:")
        for yield_data in yields:
            print(f"  {yield_data.maturity}: {yield_data.yield_value:.2f}%")
        
        # 測試資產價格
        prices = await collector.collect_asset_prices(
            symbols=["BTC-USD", "SPY"],
            days=7
        )
        print(f"\n成功採集 {len(prices)} 個資產的價格歷史:")
        for symbol, history in prices.items():
            print(f"  {symbol}: {len(history.prices)} 個數據點")
            if history.prices:
                print(f"    最新價格: ${history.prices[-1]:,.2f}")
        
        print("\n✅ 市場數據測試通過")
        return True
    except Exception as e:
        print(f"\n❌ 市場數據測試失敗: {str(e)}")
        logger.error(f"市場數據測試錯誤詳情", exc_info=True)
        return False


async def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("MacroPulse 數據採集器測試")
    print("=" * 60)
    
    results = []
    
    # 執行所有測試
    results.append(await test_polymarket())
    results.append(await test_fred())
    results.append(await test_market_data())
    
    # 總結
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ 所有測試通過！({passed}/{total})")
    else:
        print(f"⚠️  部分測試失敗 ({passed}/{total})")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

