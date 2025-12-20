"""
日誌系統模組

提供統一的日誌格式化和輸出管理。
"""

import logging
import sys
import re
from typing import Any
from datetime import datetime
from pathlib import Path


class SensitiveInfoFilter(logging.Filter):
    """過濾日誌中的敏感資訊"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        過濾敏感資訊
        
        Args:
            record: 日誌記錄
            
        Returns:
            bool: 是否允許記錄
        """
        if hasattr(record, 'msg'):
            record.msg = self._sanitize(str(record.msg))
        return True
    
    @staticmethod
    def _sanitize(message: str) -> str:
        """
        清理敏感資訊
        
        Args:
            message: 原始訊息
            
        Returns:
            str: 清理後的訊息
        """
        # 過濾 OpenAI API Key
        message = re.sub(r'sk-[a-zA-Z0-9]{32,}', 'sk-***', message)
        
        # 過濾一般 API Key
        message = re.sub(
            r'(api[_-]?key|apikey|token)["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]+', 
            r'\1=***', 
            message, 
            flags=re.IGNORECASE
        )
        
        # 過濾 Bearer Token
        message = re.sub(r'Bearer\s+[a-zA-Z0-9_-]+', 'Bearer ***', message)
        
        return message


class ColoredFormatter(logging.Formatter):
    """彩色日誌格式化器（用於控制台輸出）"""
    
    # ANSI 顏色碼
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日誌記錄
        
        Args:
            record: 日誌記錄
            
        Returns:
            str: 格式化後的日誌
        """
        # 添加顏色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )
        
        return super().format(record)


def setup_logger(
    name: str = "MacroPulse",
    log_level: str = "INFO",
    log_file: Path | None = None,
    console_output: bool = True
) -> logging.Logger:
    """
    設定日誌系統
    
    Args:
        name: Logger 名稱
        log_level: 日誌級別 (DEBUG, INFO, WARNING, ERROR)
        log_file: 日誌檔案路徑（可選）
        console_output: 是否輸出到控制台
        
    Returns:
        logging.Logger: 配置好的 Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 移除既有的 handlers
    logger.handlers.clear()
    
    # 添加敏感資訊過濾器
    sensitive_filter = SensitiveInfoFilter()
    
    # 控制台輸出
    if console_output:
        # Windows 環境需要使用 UTF-8 編碼的 StreamHandler
        if sys.platform == "win32":
            import io
            # 使用 UTF-8 編碼的 stdout
            console_handler = logging.StreamHandler(
                io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
        
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        # 使用彩色格式化器
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(sensitive_filter)
        logger.addHandler(console_handler)
    
    # 檔案輸出
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # 檔案記錄所有級別
        
        # 檔案使用簡單格式
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(sensitive_filter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    獲取已存在的 Logger
    
    Args:
        name: Logger 名稱
        
    Returns:
        logging.Logger: Logger 實例
    """
    return logging.getLogger(name)

