"""
日志工具模块
"""

import logging
import os
from datetime import datetime
from config.settings import LOG_DIR, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT


def setup_logger(name='crawler', log_file=None, level=LOG_LEVEL):
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        log_file: 日志文件路径
        level: 日志级别

    Returns:
        logging.Logger: 日志记录器对象
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 创建格式化器
    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file is None:
        log_file = os.path.join(LOG_DIR, f'crawler_{datetime.now().strftime("%Y%m%d")}.log')

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 错误日志文件处理器
    error_log_file = os.path.join(LOG_DIR, f'error_{datetime.now().strftime("%Y%m%d")}.log')
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


# 创建默认日志记录器
logger = setup_logger()
