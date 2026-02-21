"""
日期工具模块
"""

from datetime import datetime, timedelta
from typing import List
from config.settings import DATE_FORMAT


def get_current_date(fmt: str = DATE_FORMAT) -> str:
    """
    获取当前日期

    Args:
        fmt: 日期格式

    Returns:
        str: 格式化的日期字符串
    """
    return datetime.now().strftime(fmt)


def format_date(date_obj: datetime, fmt: str = DATE_FORMAT) -> str:
    """
    格式化日期对象

    Args:
        date_obj: 日期对象
        fmt: 日期格式

    Returns:
        str: 格式化的日期字符串
    """
    return date_obj.strftime(fmt)


def parse_date(date_str: str, fmt: str = DATE_FORMAT) -> datetime:
    """
    解析日期字符串

    Args:
        date_str: 日期字符串
        fmt: 日期格式

    Returns:
        datetime: 日期对象
    """
    return datetime.strptime(date_str, fmt)


def get_date_range(start_date: str, end_date: str, fmt: str = DATE_FORMAT) -> List[str]:
    """
    获取日期范围内的所有日期

    Args:
        start_date: 开始日期
        end_date: 结束日期
        fmt: 日期格式

    Returns:
        List[str]: 日期列表
    """
    start = parse_date(start_date, fmt)
    end = parse_date(end_date, fmt)

    date_list = []
    current = start

    while current <= end:
        date_list.append(format_date(current, fmt))
        current += timedelta(days=1)

    return date_list


def get_days_between(start_date: str, end_date: str, fmt: str = DATE_FORMAT) -> int:
    """
    计算两个日期之间的天数

    Args:
        start_date: 开始日期
        end_date: 结束日期
        fmt: 日期格式

    Returns:
        int: 天数
    """
    start = parse_date(start_date, fmt)
    end = parse_date(end_date, fmt)
    return (end - start).days + 1


def get_month_range(year: int = None, month: int = None) -> tuple:
    """
    获取指定月份的日期范围

    Args:
        year: 年份，默认当前年
        month: 月份，默认当前月

    Returns:
        tuple: (开始日期, 结束日期)
    """
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    # 月份第一天
    start_date = datetime(year, month, 1)

    # 月份最后一天
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

    return (format_date(start_date), format_date(end_date))


def get_recent_days(days: int = 7) -> tuple:
    """
    获取最近N天的日期范围

    Args:
        days: 天数

    Returns:
        tuple: (开始日期, 结束日期)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days - 1)

    return (format_date(start_date), format_date(end_date))
