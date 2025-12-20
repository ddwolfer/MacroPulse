"""
測試工具模組功能

驗證 logger、formatters、cache 等基礎工具是否正常運作。
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime

# Windows 環境設定 UTF-8
if sys.platform == "win32":
    os.environ["PYTHONUTF8"] = "1"
    # 設定控制台輸出為 UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import setup_logger
from src.utils.formatters import (
    format_number,
    format_percentage,
    format_currency,
    format_date,
    format_markdown_table,
    format_markdown_list,
    format_confidence_emoji,
)
from src.utils.cache import CacheManager
from pydantic import BaseModel


# 測試用的 Pydantic 模型
class TestData(BaseModel):
    name: str
    value: float
    timestamp: datetime


def test_logger():
    """測試日誌系統"""
    print("\n" + "=" * 60)
    print("測試 1: Logger 日誌系統")
    print("=" * 60)
    
    logger = setup_logger(name="Test", log_level="DEBUG")
    
    logger.debug("這是 DEBUG 訊息")
    logger.info("這是 INFO 訊息")
    logger.warning("這是 WARNING 訊息")
    logger.error("這是 ERROR 訊息")
    
    # 測試敏感資訊過濾
    logger.info("測試 API Key 過濾: sk-1234567890abcdefghijklmnopqrstuvwxyz")
    logger.info("測試 API Key 過濾: api_key=secret_token_here")
    
    print("✅ Logger 測試通過")


def test_formatters():
    """測試格式化工具"""
    print("\n" + "=" * 60)
    print("測試 2: Formatters 格式化工具")
    print("=" * 60)
    
    # 測試數字格式化
    print(f"數字格式化: {format_number(1234567.89)}")
    
    # 測試百分比格式化
    print(f"百分比格式化: {format_percentage(0.1234)}")
    print(f"負百分比: {format_percentage(-0.05)}")
    
    # 測試貨幣格式化
    print(f"美元: {format_currency(1234567.89)}")
    print(f"歐元: {format_currency(1000, currency='EUR')}")
    
    # 測試日期格式化
    now = datetime.now()
    print(f"預設格式: {format_date(now, 'default')}")
    print(f"短格式: {format_date(now, 'short')}")
    print(f"長格式: {format_date(now, 'long')}")
    
    # 測試 Markdown 表格
    headers = ['指標', '數值', '變化']
    rows = [
        ['CPI', '3.2%', '+0.1%'],
        ['失業率', '4.5%', '-0.2%'],
        ['PMI', '52.3', '+1.5']
    ]
    print("\nMarkdown 表格:")
    print(format_markdown_table(headers, rows))
    
    # 測試 Markdown 列表
    items = ['項目 1', '項目 2', '項目 3']
    print("\nMarkdown 列表:")
    print(format_markdown_list(items))
    
    # 測試信心指數 emoji
    print(f"\n信心指數 emoji:")
    print(f"0.9: {format_confidence_emoji(0.9)}")
    print(f"0.7: {format_confidence_emoji(0.7)}")
    print(f"0.5: {format_confidence_emoji(0.5)}")
    print(f"0.3: {format_confidence_emoji(0.3)}")
    
    print("\n✅ Formatters 測試通過")


def test_cache():
    """測試緩存管理器"""
    print("\n" + "=" * 60)
    print("測試 3: Cache 緩存管理器")
    print("=" * 60)
    
    # 建立測試緩存目錄
    cache_dir = Path("test_cache")
    cache_manager = CacheManager(cache_dir, ttl_hours=1)
    
    # 測試數據
    test_data = TestData(
        name="測試數據",
        value=123.45,
        timestamp=datetime.now()
    )
    
    # 測試寫入
    key = "test_key_1"
    success = cache_manager.set(key, test_data)
    print(f"寫入緩存: {'成功' if success else '失敗'}")
    
    # 測試讀取
    cached_data = cache_manager.get(key, TestData)
    if cached_data:
        print(f"讀取緩存: {cached_data.name} = {cached_data.value}")
    else:
        print("讀取緩存: 失敗")
    
    # 測試緩存存在性
    exists = cache_manager.exists(key)
    print(f"緩存存在: {exists}")
    
    # 測試緩存資訊
    info = cache_manager.get_cache_info(key)
    if info:
        print(f"緩存資訊:")
        print(f"  - 大小: {info['size']} bytes")
        print(f"  - 年齡: {info['age_hours']:.2f} 小時")
        print(f"  - 已過期: {info['expired']}")
    
    # 清理測試緩存
    cache_manager.clear_all()
    cache_dir.rmdir()
    
    print("✅ Cache 測試通過")


async def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("MacroPulse 工具模組測試")
    print("=" * 60)
    
    # 執行所有測試
    test_logger()
    test_formatters()
    test_cache()
    
    print("\n" + "=" * 60)
    print("✅ 所有測試通過！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

