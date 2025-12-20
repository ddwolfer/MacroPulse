"""
市場數據採集器

使用 yfinance 採集美債殖利率和資產價格數據。
參考文件：SPEC_API_Integrations.md, SPEC_Data_Models.md
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta

import yfinance as yf
import pandas as pd

from src.collectors.base_collector import BaseCollector
from src.schema.models import TreasuryYield, AssetPriceHistory
from config import settings

logger = logging.getLogger(__name__)


class MarketDataCollector(BaseCollector):
    """市場數據採集器（美債、股票、加密貨幣）"""
    
    # 美債 Ticker 符號
    TREASURY_TICKERS = {
        "^IRX": "3M",    # 3 個月
        "^FVX": "5Y",    # 5 年期
        "^TNX": "10Y",   # 10 年期
        "^TYX": "30Y"    # 30 年期
    }
    
    # 主要資產 Ticker
    ASSET_TICKERS = [
        "BTC-USD",  # Bitcoin
        "ETH-USD",  # Ethereum
        "SPY",      # S&P 500 ETF
        "QQQ",      # Nasdaq 100 ETF
        "DX-Y.NYB"  # 美元指數
    ]
    
    def __init__(self):
        # yfinance 數據變化快，TTL 設定為 15 分鐘
        super().__init__(cache_ttl_hours=0)  # 轉換為分鐘
        # 重新設定緩存 TTL 為分鐘
        self.cache_manager.ttl = timedelta(minutes=settings.yfinance_cache_ttl)
    
    async def collect_treasury_yields(self) -> List[TreasuryYield]:
        """
        採集美債殖利率數據
        
        Returns:
            List[TreasuryYield]: 殖利率列表
        """
        logger.info("開始採集美債殖利率數據")
        
        yields = []
        for ticker, maturity in self.TREASURY_TICKERS.items():
            try:
                yield_data = await self._fetch_yield(ticker, maturity)
                if yield_data:
                    yields.append(yield_data)
            except Exception as e:
                logger.warning(f"採集 {ticker} 失敗：{str(e)}")
                continue
        
        logger.info(f"成功採集 {len(yields)} 個美債殖利率")
        return yields
    
    async def _fetch_yield(self, ticker: str, maturity: str) -> Optional[TreasuryYield]:
        """
        獲取單一殖利率數據
        
        Args:
            ticker: Yahoo Finance ticker
            maturity: 到期期限（如 "10Y"）
            
        Returns:
            Optional[TreasuryYield]: 殖利率數據
        """
        # 檢查緩存
        cache_key = self.get_cache_key(ticker)
        cached_data = self.cache_manager.get_raw(cache_key)
        
        if cached_data:
            logger.debug(f"使用緩存的殖利率數據：{ticker}")
            try:
                return TreasuryYield(**cached_data)
            except Exception as e:
                logger.warning(f"緩存數據解析失敗：{str(e)}")
        
        try:
            # yfinance 是同步的，但我們在 async 函數中使用
            # 在生產環境中可以使用 asyncio.to_thread
            data = yf.Ticker(ticker)
            hist = data.history(period="1d")
            
            if hist.empty:
                logger.warning(f"沒有數據：{ticker}")
                return None
            
            latest_close = float(hist['Close'].iloc[-1])
            timestamp = hist.index[-1].to_pydatetime()
            
            yield_obj = TreasuryYield(
                symbol=ticker,
                maturity=maturity,
                yield_value=latest_close,
                timestamp=timestamp
            )
            
            # 寫入緩存
            self.cache_manager.set(cache_key, yield_obj.model_dump())
            
            logger.debug(f"成功採集殖利率：{ticker} = {latest_close}%")
            return yield_obj
            
        except Exception as e:
            logger.error(f"採集殖利率失敗 {ticker}：{str(e)}")
            return None
    
    async def collect_asset_prices(
        self,
        symbols: Optional[List[str]] = None,
        days: int = 7
    ) -> Dict[str, AssetPriceHistory]:
        """
        採集資產價格歷史數據
        
        Args:
            symbols: 資產符號列表（None 則使用預設列表）
            days: 歷史天數
            
        Returns:
            Dict[str, AssetPriceHistory]: {symbol: price_history}
        """
        if symbols is None:
            symbols = self.ASSET_TICKERS
        
        # 添加用戶持倉的資產
        user_portfolio = settings.get_user_portfolio_list()
        for holding in user_portfolio:
            symbol = holding.get("symbol", "")
            if symbol and symbol not in symbols:
                symbols.append(symbol)
        
        logger.info(f"開始採集資產價格歷史（{len(symbols)} 個資產，{days} 天）")
        
        results = {}
        for symbol in symbols:
            try:
                price_history = await self._fetch_price_history(symbol, days)
                if price_history:
                    results[symbol] = price_history
            except Exception as e:
                logger.warning(f"採集 {symbol} 失敗：{str(e)}")
                continue
        
        logger.info(f"成功採集 {len(results)} 個資產的價格歷史")
        return results
    
    async def _fetch_price_history(
        self,
        symbol: str,
        days: int
    ) -> Optional[AssetPriceHistory]:
        """
        獲取單一資產的價格歷史
        
        Args:
            symbol: 資產符號
            days: 歷史天數
            
        Returns:
            Optional[AssetPriceHistory]: 價格歷史
        """
        # 檢查緩存
        cache_key = self.get_cache_key(f"{symbol}_{days}d")
        cached_data = self.cache_manager.get_raw(cache_key)
        
        if cached_data:
            logger.debug(f"使用緩存的價格歷史：{symbol}")
            try:
                return AssetPriceHistory(**cached_data)
            except Exception as e:
                logger.warning(f"緩存數據解析失敗：{str(e)}")
        
        try:
            data = yf.Ticker(symbol)
            hist = data.history(period=f"{days}d")
            
            if hist.empty or len(hist) < 2:
                logger.warning(f"數據不足：{symbol}")
                return None
            
            prices = hist['Close'].tolist()
            dates = [d.date() for d in hist.index]
            
            price_history = AssetPriceHistory(
                symbol=symbol,
                prices=prices,
                dates=dates
            )
            
            # 寫入緩存
            self.cache_manager.set(cache_key, price_history.model_dump())
            
            logger.debug(f"成功採集價格歷史：{symbol}（{len(prices)} 個數據點）")
            return price_history
            
        except Exception as e:
            logger.error(f"採集價格歷史失敗 {symbol}：{str(e)}")
            return None

