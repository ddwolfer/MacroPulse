"""
Polymarket 數據採集器

從 Polymarket Gamma API 採集預測市場數據。
參考文件：SPEC_API_Integrations.md, SPEC_Data_Models.md
"""

import logging
from typing import List, Optional
from datetime import datetime

from src.collectors.base_collector import BaseCollector
from src.schema.models import PolymarketMarket, PolymarketToken
from config import settings

logger = logging.getLogger(__name__)


class PolymarketCollector(BaseCollector):
    """Polymarket 預測市場數據採集器"""
    
    BASE_URL = "https://gamma-api.polymarket.com"
    
    def __init__(self):
        # Polymarket 數據變化快，TTL 設定為 1 小時
        super().__init__(cache_ttl_hours=settings.polymarket_cache_ttl)
    
    async def collect(self, limit: int = 20, category: str = "Macro") -> List[PolymarketMarket]:
        """
        採集 Polymarket 市場數據
        
        Args:
            limit: 返回市場數量
            category: 市場類別（Macro, Politics, Crypto）
            
        Returns:
            List[PolymarketMarket]: 市場數據列表
        """
        logger.info(f"開始採集 Polymarket 市場數據（類別：{category}，數量：{limit}）")
        
        # 檢查緩存
        cache_key = self.get_cache_key(f"markets_{category}_{limit}")
        cached_data = self.cache_manager.get_raw(cache_key)
        
        if cached_data:
            logger.info(f"使用緩存的 Polymarket 數據")
            try:
                return [PolymarketMarket(**market) for market in cached_data]
            except Exception as e:
                logger.warning(f"緩存數據解析失敗：{str(e)}")
        
        # 從 API 獲取
        try:
            markets = await self._fetch_markets(limit)
            
            # 過濾和處理
            filtered_markets = self._filter_markets(markets)
            
            # 寫入緩存
            if filtered_markets:
                cache_data = [market.model_dump() for market in filtered_markets]
                self.cache_manager.set(cache_key, cache_data)
            
            logger.info(f"成功採集 {len(filtered_markets)} 個 Polymarket 市場")
            return filtered_markets
            
        except Exception as e:
            logger.error(f"Polymarket 數據採集失敗：{str(e)}")
            return []
    
    async def _fetch_markets(self, limit: int) -> List[dict]:
        """
        從 API 獲取市場列表
        
        Args:
            limit: 返回數量
            
        Returns:
            List[dict]: 原始市場數據
        """
        url = f"{self.BASE_URL}/markets"
        params = {
            "active": "true",
            "closed": "false",
            "limit": limit
        }
        
        response = await self.fetch_with_retry(url, params=params)
        
        if not response:
            logger.warning("無法從 Polymarket API 獲取數據")
            return []
        
        try:
            data = response.json()
            # 處理不同的 API 響應格式
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("data", [])
            else:
                logger.warning(f"未預期的 API 響應格式：{type(data)}")
                return []
        except Exception as e:
            logger.error(f"解析 Polymarket API 響應失敗：{str(e)}")
            return []
    
    def _filter_markets(self, markets: List[dict]) -> List[PolymarketMarket]:
        """
        過濾和處理市場數據
        
        Args:
            markets: 原始市場數據
            
        Returns:
            List[PolymarketMarket]: 過濾後的市場數據
        """
        filtered = []
        
        for market in markets:
            try:
                # 檢查交易量門檻
                volume = float(market.get("volume", 0))
                if volume < settings.polymarket_min_volume:
                    continue
                
                # 解析代幣
                tokens = []
                for token in market.get("tokens", []):
                    try:
                        tokens.append(PolymarketToken(
                            outcome=token.get("outcome", ""),
                            price=float(token.get("price", 0)),
                            volume=float(token.get("volume", 0))
                        ))
                    except Exception as e:
                        logger.warning(f"解析代幣失敗：{str(e)}")
                        continue
                
                if not tokens:
                    continue
                
                # 解析結束日期
                end_date = None
                if market.get("endDate"):
                    try:
                        end_date = datetime.fromisoformat(
                            market["endDate"].replace("Z", "+00:00")
                        )
                    except Exception:
                        pass
                
                # 建立市場物件
                market_obj = PolymarketMarket(
                    id=market.get("id", ""),
                    question=market.get("question", ""),
                    slug=market.get("slug", ""),
                    category=market.get("category", ""),
                    volume=volume,
                    liquidity=float(market.get("liquidity", 0)),
                    active=market.get("active", True),
                    end_date=end_date,
                    tokens=tokens,
                    price_change_7d=None  # TODO: 需要額外 API 呼叫獲取歷史數據
                )
                
                filtered.append(market_obj)
                
            except Exception as e:
                logger.warning(f"處理市場數據失敗：{str(e)}")
                continue
        
        return filtered

