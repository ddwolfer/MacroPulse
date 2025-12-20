"""
緩存管理模組

提供數據緩存的讀寫、過期檢查等功能。
參考文件：SPEC_Error_Handling.md
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, TypeVar, Type, Any
from pydantic import BaseModel
import json
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class CacheManager:
    """緩存管理器"""
    
    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        """
        初始化緩存管理器
        
        Args:
            cache_dir: 緩存目錄
            ttl_hours: 緩存有效期（小時）
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        logger.debug(f"初始化緩存管理器：{cache_dir}，TTL={ttl_hours}小時")
    
    def get_cache_path(self, key: str) -> Path:
        """
        生成緩存檔案路徑
        
        Args:
            key: 緩存鍵
            
        Returns:
            Path: 緩存檔案路徑
        """
        # 清理不安全的字符
        safe_key = key.replace("/", "_").replace(":", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_key}.json"
    
    def get(self, key: str, model_class: Type[T]) -> Optional[T]:
        """
        從緩存讀取數據
        
        Args:
            key: 緩存鍵
            model_class: Pydantic 模型類別
            
        Returns:
            Optional[T]: 如果緩存有效則返回數據，否則返回 None
        """
        cache_path = self.get_cache_path(key)
        
        if not cache_path.exists():
            logger.debug(f"緩存未命中：{key}")
            return None
        
        # 檢查是否過期
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        
        if age > self.ttl:
            logger.info(f"緩存已過期：{key}（{age.total_seconds() / 3600:.1f}小時）")
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 使用 Pydantic 驗證數據
            cached_data = model_class(**data)
            logger.debug(f"緩存命中：{key}")
            return cached_data
            
        except json.JSONDecodeError as e:
            logger.warning(f"緩存 JSON 解析失敗 {key}：{str(e)}")
            return None
        except Exception as e:
            logger.warning(f"讀取緩存失敗 {key}：{str(e)}")
            return None
    
    def get_raw(self, key: str) -> Optional[dict]:
        """
        從緩存讀取原始 JSON 數據（不經過 Pydantic 驗證）
        
        Args:
            key: 緩存鍵
            
        Returns:
            Optional[dict]: 如果緩存有效則返回數據，否則返回 None
        """
        cache_path = self.get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        # 檢查是否過期
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime > self.ttl:
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"讀取原始緩存失敗 {key}：{str(e)}")
            return None
    
    def set(self, key: str, data: BaseModel | dict | list) -> bool:
        """
        寫入緩存
        
        Args:
            key: 緩存鍵
            data: 要緩存的數據（Pydantic 模型或 dict/list）
            
        Returns:
            bool: 是否成功寫入
        """
        cache_path = self.get_cache_path(key)
        
        try:
            # 如果是 Pydantic 模型，轉換為 dict
            if isinstance(data, BaseModel):
                data_dict = data.model_dump()
            else:
                data_dict = data
            
            # 寫入檔案
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False, default=str)
            
            logger.debug(f"緩存已寫入：{key}")
            return True
            
        except Exception as e:
            logger.error(f"寫入緩存失敗 {key}：{str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        檢查緩存是否存在且未過期
        
        Args:
            key: 緩存鍵
            
        Returns:
            bool: 緩存是否存在且有效
        """
        cache_path = self.get_cache_path(key)
        
        if not cache_path.exists():
            return False
        
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - mtime <= self.ttl
    
    def delete(self, key: str) -> bool:
        """
        刪除緩存
        
        Args:
            key: 緩存鍵
            
        Returns:
            bool: 是否成功刪除
        """
        cache_path = self.get_cache_path(key)
        
        try:
            if cache_path.exists():
                cache_path.unlink()
                logger.debug(f"緩存已刪除：{key}")
                return True
            return False
        except Exception as e:
            logger.error(f"刪除緩存失敗 {key}：{str(e)}")
            return False
    
    def clear_all(self) -> int:
        """
        清空所有緩存
        
        Returns:
            int: 刪除的檔案數量
        """
        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                count += 1
            logger.info(f"已清空所有緩存：{count} 個檔案")
            return count
        except Exception as e:
            logger.error(f"清空緩存失敗：{str(e)}")
            return count
    
    def clear_expired(self) -> int:
        """
        清理過期的緩存
        
        Returns:
            int: 刪除的檔案數量
        """
        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if datetime.now() - mtime > self.ttl:
                    cache_file.unlink()
                    count += 1
            
            if count > 0:
                logger.info(f"已清理過期緩存：{count} 個檔案")
            return count
        except Exception as e:
            logger.error(f"清理過期緩存失敗：{str(e)}")
            return count
    
    def get_cache_info(self, key: str) -> Optional[dict]:
        """
        獲取緩存資訊
        
        Args:
            key: 緩存鍵
            
        Returns:
            Optional[dict]: 緩存資訊（存在時間、大小等）
        """
        cache_path = self.get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        stat = cache_path.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        age = datetime.now() - mtime
        
        return {
            'key': key,
            'path': str(cache_path),
            'size': stat.st_size,
            'created': mtime.isoformat(),
            'age_hours': age.total_seconds() / 3600,
            'expired': age > self.ttl
        }

