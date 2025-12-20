"""
格式化工具模組

提供 Markdown、數字、日期等格式化功能。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json


def format_number(
    value: float, 
    decimal_places: int = 2, 
    add_comma: bool = True
) -> str:
    """
    格式化數字
    
    Args:
        value: 數值
        decimal_places: 小數位數
        add_comma: 是否添加千分位符號
        
    Returns:
        str: 格式化後的字串
        
    Example:
        >>> format_number(1234567.89)
        '1,234,567.89'
        >>> format_number(0.1234, decimal_places=4)
        '0.1234'
    """
    if add_comma:
        return f"{value:,.{decimal_places}f}"
    return f"{value:.{decimal_places}f}"


def format_percentage(
    value: float, 
    decimal_places: int = 2, 
    add_sign: bool = True
) -> str:
    """
    格式化百分比
    
    Args:
        value: 數值（0.1234 表示 12.34%）
        decimal_places: 小數位數
        add_sign: 是否添加正負號
        
    Returns:
        str: 格式化後的百分比字串
        
    Example:
        >>> format_percentage(0.1234)
        '+12.34%'
        >>> format_percentage(-0.05)
        '-5.00%'
    """
    percentage = value * 100
    sign = '+' if value > 0 and add_sign else ''
    return f"{sign}{percentage:.{decimal_places}f}%"


def format_currency(
    value: float, 
    currency: str = "USD", 
    decimal_places: int = 2
) -> str:
    """
    格式化貨幣
    
    Args:
        value: 金額
        currency: 貨幣符號
        decimal_places: 小數位數
        
    Returns:
        str: 格式化後的貨幣字串
        
    Example:
        >>> format_currency(1234567.89)
        '$1,234,567.89'
        >>> format_currency(1000, currency="EUR")
        '€1,000.00'
    """
    currency_symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'CNY': '¥'
    }
    
    symbol = currency_symbols.get(currency.upper(), currency)
    return f"{symbol}{value:,.{decimal_places}f}"


def format_date(
    date: datetime, 
    format_type: str = "default"
) -> str:
    """
    格式化日期
    
    Args:
        date: datetime 物件
        format_type: 格式類型 ('default', 'short', 'long', 'iso')
        
    Returns:
        str: 格式化後的日期字串
        
    Example:
        >>> format_date(datetime.now(), 'default')
        '2024-12-20 15:30:00'
        >>> format_date(datetime.now(), 'short')
        '2024-12-20'
    """
    formats = {
        'default': '%Y-%m-%d %H:%M:%S',
        'short': '%Y-%m-%d',
        'long': '%Y年%m月%d日 %H:%M:%S',
        'iso': '%Y-%m-%dT%H:%M:%SZ'
    }
    
    return date.strftime(formats.get(format_type, formats['default']))


def format_markdown_table(
    headers: List[str], 
    rows: List[List[Any]], 
    alignments: Optional[List[str]] = None
) -> str:
    """
    生成 Markdown 表格
    
    Args:
        headers: 表頭列表
        rows: 數據行列表
        alignments: 對齊方式列表 ('left', 'center', 'right')
        
    Returns:
        str: Markdown 表格字串
        
    Example:
        >>> headers = ['名稱', '數值', '變化']
        >>> rows = [['CPI', '3.2%', '+0.1%'], ['失業率', '4.5%', '-0.2%']]
        >>> print(format_markdown_table(headers, rows))
        | 名稱 | 數值 | 變化 |
        |------|------|------|
        | CPI | 3.2% | +0.1% |
        | 失業率 | 4.5% | -0.2% |
    """
    if not headers or not rows:
        return ""
    
    # 預設左對齊
    if not alignments:
        alignments = ['left'] * len(headers)
    
    # 生成表頭
    header_row = '| ' + ' | '.join(headers) + ' |'
    
    # 生成分隔行
    separator_parts = []
    for align in alignments:
        if align == 'center':
            separator_parts.append(':---:')
        elif align == 'right':
            separator_parts.append('---:')
        else:
            separator_parts.append('---')
    separator_row = '| ' + ' | '.join(separator_parts) + ' |'
    
    # 生成數據行
    data_rows = []
    for row in rows:
        row_str = '| ' + ' | '.join(str(cell) for cell in row) + ' |'
        data_rows.append(row_str)
    
    return '\n'.join([header_row, separator_row] + data_rows)


def format_markdown_list(
    items: List[str], 
    ordered: bool = False, 
    indent_level: int = 0
) -> str:
    """
    生成 Markdown 列表
    
    Args:
        items: 列表項目
        ordered: 是否為有序列表
        indent_level: 縮排層級
        
    Returns:
        str: Markdown 列表字串
        
    Example:
        >>> items = ['項目 1', '項目 2', '項目 3']
        >>> print(format_markdown_list(items))
        - 項目 1
        - 項目 2
        - 項目 3
    """
    indent = '  ' * indent_level
    lines = []
    
    for i, item in enumerate(items, 1):
        if ordered:
            lines.append(f"{indent}{i}. {item}")
        else:
            lines.append(f"{indent}- {item}")
    
    return '\n'.join(lines)


def format_markdown_code_block(
    code: str, 
    language: str = ""
) -> str:
    """
    生成 Markdown 代碼塊
    
    Args:
        code: 代碼內容
        language: 語言標識
        
    Returns:
        str: Markdown 代碼塊字串
    """
    return f"```{language}\n{code}\n```"


def format_json_pretty(data: Dict | List) -> str:
    """
    美化 JSON 輸出
    
    Args:
        data: JSON 數據
        
    Returns:
        str: 格式化後的 JSON 字串
    """
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def truncate_text(
    text: str, 
    max_length: int = 100, 
    suffix: str = "..."
) -> str:
    """
    截斷文字
    
    Args:
        text: 原始文字
        max_length: 最大長度
        suffix: 截斷後綴
        
    Returns:
        str: 截斷後的文字
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_confidence_emoji(confidence: float) -> str:
    """
    根據信心指數返回對應的 emoji
    
    Args:
        confidence: 信心指數 (0.0-1.0)
        
    Returns:
        str: Emoji 字符
        
    Example:
        >>> format_confidence_emoji(0.9)
        '🟢'
        >>> format_confidence_emoji(0.5)
        '🟡'
    """
    if confidence >= 0.8:
        return '🟢'  # 高信心
    elif confidence >= 0.6:
        return '🟡'  # 中等信心
    elif confidence >= 0.4:
        return '🟠'  # 偏低信心
    else:
        return '🔴'  # 低信心

