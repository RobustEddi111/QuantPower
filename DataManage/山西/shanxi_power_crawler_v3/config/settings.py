"""
配置文件
"""

import os

# ==================== 基础配置 ====================

# 基础URL
BASE_URL = "https://pmos.sx.sgcc.com.cn"

# 日前节点电价接口
NODE_PRICE_API = "/px-sy-retailsettlement-sx/resource/dayNodePrice"

# 请求头模板（Cookie会动态设置）
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Content-Type': 'application/json;charset=UTF-8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://pmos.sx.sgcc.com.cn/',
    'Origin': 'https://pmos.sx.sgcc.com.cn'
}

# ==================== 请求配置 ====================

# 超时时间（秒）
TIMEOUT = 15

# 最大重试次数
MAX_RETRIES = 3

# 请求间隔（秒）
REQUEST_DELAY = 1

# 分页大小
PAGE_SIZE = 100

# ==================== 代理配置 ====================

# 是否使用代理
USE_PROXY = False

# 代理服务器
PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}

# ==================== 目录配置 ====================

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, "data")
EXCEL_DIR = os.path.join(DATA_DIR, "excel")
CSV_DIR = os.path.join(DATA_DIR, "csv")
JSON_DIR = os.path.join(DATA_DIR, "json")

# 日志目录
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 节点配置文件
NODES_CONFIG_FILE = os.path.join(BASE_DIR, "nodes.json")

# ==================== 日志配置 ====================

# 日志级别
LOG_LEVEL = "INFO"

# 日志格式
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 日志日期格式
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ==================== 数据配置 ====================

# 默认日期格式
DATE_FORMAT = "%Y-%m-%d"

# Excel引擎
EXCEL_ENGINE = "openpyxl"

# CSV编码
CSV_ENCODING = "utf-8-sig"

# ==================== Cookie配置 ====================

# Cookie过期提示关键词
COOKIE_EXPIRED_KEYWORDS = ['登录', '会话', '认证', '授权', '401', '403']

# ==================== 创建必要目录 ====================

def create_directories():
    """创建必要的目录"""
    dirs = [DATA_DIR, EXCEL_DIR, CSV_DIR, JSON_DIR, LOG_DIR]
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)

# 自动创建目录
create_directories()
