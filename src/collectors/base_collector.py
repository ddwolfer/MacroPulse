"""
基礎採集器

提供統一的 HTTP 請求邏輯、重試機制和錯誤處理。
參考文件：SPEC_Error_Handling.md, SPEC_API_Integrations.md
"""

import asyncio
import logging
from typing import Optional, Any, Callable
from abc import ABC, abstractmethod

import httpx

from config import settings
from src.utils.cache import CacheManager

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    基礎採集器抽象類別
    
    提供：
    - 統一的 HTTP 請求邏輯
    - 指數退避重試機制
    - 緩存管理
    - 錯誤處理
    """
    
    def __init__(self, cache_ttl_hours: int = 24):
        """
        初始化採集器
        
        Args:
            cache_ttl_hours: 緩存有效期（小時）
        """
        self.cache_manager = CacheManager(
            settings.data_cache_dir / self.__class__.__name__.lower(),
            ttl_hours=cache_ttl_hours
        )
        self.timeout = settings.request_timeout
        self.max_retries = settings.max_retries
        logger.debug(f"初始化 {self.__class__.__name__}")
    
    async def fetch_with_retry(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None
    ) -> Optional[httpx.Response]:
        """
        帶重試機制的 HTTP GET 請求
        
        Args:
            url: 請求 URL
            params: 查詢參數
            headers: 請求標頭
            
        Returns:
            Optional[httpx.Response]: 響應物件，失敗則返回 None
        """
        async def _fetch():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response
        
        return await self._retry_with_exponential_backoff(_fetch)
    
    async def _retry_with_exponential_backoff(
        self,
        func: Callable,
        exceptions: tuple = (httpx.HTTPStatusError, httpx.TimeoutException, httpx.NetworkError)
    ) -> Optional[Any]:
        """
        指數退避重試機制
        
        Args:
            func: 要執行的異步函數
            exceptions: 要捕獲的異常類型
            
        Returns:
            函數返回值，如果所有重試都失敗則返回 None
        """
        delay = settings.retry_initial_delay
        
        for attempt in range(self.max_retries):
            try:
                return await func()
            except exceptions as e:
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"{self.__class__.__name__} 重試 {self.max_retries} 次後仍然失敗: {str(e)}"
                    )
                    return None
                
                # 特殊處理 HTTP 429 (Rate Limit)
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 429:
                    wait_time = 60  # Rate Limit 等待 60 秒
                    logger.warning(
                        f"{self.__class__.__name__} 遇到 Rate Limit，等待 {wait_time} 秒..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                
                logger.warning(
                    f"{self.__class__.__name__} 嘗試 {attempt + 1}/{self.max_retries} 失敗: {str(e)}. "
                    f"等待 {delay:.2f} 秒後重試..."
                )
                await asyncio.sleep(delay)
                delay = min(delay * settings.retry_backoff_factor, 60.0)
            except Exception as e:
                logger.error(f"{self.__class__.__name__} 發生未預期的錯誤: {str(e)}")
                return None
        
        return None
    
    @abstractmethod
    async def collect(self) -> Any:
        """
        採集數據的抽象方法
        
        子類別必須實作此方法。
        
        Returns:
            採集到的數據
        """
        pass
    
    def get_cache_key(self, identifier: str) -> str:
        """
        生成緩存鍵
        
        Args:
            identifier: 識別符（如 series_id, market_id）
            
        Returns:
            str: 緩存鍵
        """
        from datetime import date as date_type
        today = date_type.today().isoformat()
        return f"{identifier}_{today}"

