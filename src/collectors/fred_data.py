"""
FRED 經濟數據採集器

從 FRED API 採集經濟指標數據。
參考文件：SPEC_API_Integrations.md, SPEC_Data_Models.md
"""

import logging
from typing import List, Optional
from datetime import datetime
from datetime import date as date_type

from src.collectors.base_collector import BaseCollector
from src.schema.models import FREDSeries, FREDObservation
from config import settings

logger = logging.getLogger(__name__)


class FREDCollector(BaseCollector):
    """FRED 經濟數據採集器"""
    
    BASE_URL = "https://api.stlouisfed.org/fred"
    
    # 必要的經濟指標系列代碼
    SERIES_IDS = {
        "CPIAUCSL": "Consumer Price Index",
        "UNRATE": "Unemployment Rate",
        "PAYEMS": "Non-Farm Payroll",
        "PCEPI": "PCE Price Index",
        "DGS10": "10-Year Treasury Yield",
        "DGS2": "2-Year Treasury Yield"
    }
    
    def __init__(self):
        # FRED 數據更新頻率低，TTL 設定為 24 小時
        super().__init__(cache_ttl_hours=settings.fred_cache_ttl)
        
        if not settings.fred_api_key:
            logger.error("缺少 FRED_API_KEY")
            raise ValueError("必須設定 FRED_API_KEY")
    
    async def collect(self, series_ids: Optional[List[str]] = None) -> dict:
        """
        採集 FRED 經濟數據
        
        Args:
            series_ids: 要採集的系列代碼列表（None 則使用預設列表）
            
        Returns:
            dict: {series_id: FREDSeries} 字典
        """
        if series_ids is None:
            series_ids = list(self.SERIES_IDS.keys())
        
        logger.info(f"開始採集 FRED 經濟數據（{len(series_ids)} 個系列）")
        
        results = {}
        for series_id in series_ids:
            try:
                series = await self._fetch_series(series_id)
                if series:
                    results[series_id] = series
            except Exception as e:
                logger.warning(f"採集 {series_id} 失敗：{str(e)}")
                continue
        
        logger.info(f"成功採集 {len(results)} 個 FRED 系列")
        return results
    
    async def _fetch_series(self, series_id: str) -> Optional[FREDSeries]:
        """
        獲取單一系列數據
        
        Args:
            series_id: 系列代碼
            
        Returns:
            Optional[FREDSeries]: 系列數據
        """
        # 檢查緩存
        cache_key = self.get_cache_key(series_id)
        cached_data = self.cache_manager.get_raw(cache_key)
        
        if cached_data:
            logger.debug(f"使用緩存的 FRED 數據：{series_id}")
            try:
                return FREDSeries(**cached_data)
            except Exception as e:
                logger.warning(f"緩存數據解析失敗：{str(e)}")
        
        # 從 API 獲取
        url = f"{self.BASE_URL}/series/observations"
        params = {
            "series_id": series_id,
            "api_key": settings.fred_api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 100  # 獲取最近 100 個觀測值
        }
        
        response = await self.fetch_with_retry(url, params=params)
        
        if not response:
            logger.warning(f"無法從 FRED API 獲取數據：{series_id}")
            return None
        
        try:
            data = response.json()
            observations_data = data.get("observations", [])
            
            # 解析觀測值
            observations = []
            for obs in observations_data:
                try:
                    value = obs.get("value")
                    if value == ".":
                        value = None
                    else:
                        value = float(value) if value else None
                    
                    observations.append(FREDObservation(
                        date=date_type.fromisoformat(obs["date"]),
                        value=value,
                        realtime_start=date_type.fromisoformat(obs["realtime_start"]),
                        realtime_end=date_type.fromisoformat(obs["realtime_end"])
                    ))
                except Exception as e:
                    logger.warning(f"解析觀測值失敗：{str(e)}")
                    continue
            
            if not observations:
                logger.warning(f"沒有有效的觀測值：{series_id}")
                return None
            
            # 建立系列物件
            series = FREDSeries(
                series_id=series_id,
                title=self.SERIES_IDS.get(series_id, series_id),
                observations=observations,
                units="",
                frequency="",
                last_updated=datetime.now()
            )
            
            # 寫入緩存
            self.cache_manager.set(cache_key, series.model_dump())
            
            logger.debug(f"成功採集 FRED 系列：{series_id}")
            return series
            
        except Exception as e:
            logger.error(f"解析 FRED API 響應失敗：{str(e)}")
            return None

