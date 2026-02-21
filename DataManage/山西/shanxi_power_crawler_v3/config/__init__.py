"""
配置模块初始化文件
"""

from .settings import *

__all__ = [
    'BASE_URL', 'HEADERS', 'TIMEOUT', 'MAX_RETRIES',
    'REQUEST_DELAY', 'DATA_DIR', 'LOG_DIR'
]
