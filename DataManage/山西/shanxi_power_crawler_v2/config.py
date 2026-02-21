# config.py
"""
配置文件 - 支持默认值和交互输入
"""

# ==================== Cookie配置 ====================
# 方式1: 直接配置（不推荐，有安全风险）
COOKIES = ""  # 留空则使用交互输入

# 方式2: 从环境变量读取（推荐）
import os
COOKIES = os.getenv('SHANXI_COOKIES', '')

# 方式3: 从文件读取（推荐）
COOKIE_FILE = "cookies.txt"  # Cookie文件路径


# ==================== 节点配置 ====================
# 默认节点列表
DEFAULT_NODES = [
    "华北.太二/500kV.2母线",
    "山西.麻田光伏电站/220kV.A母线",
    "山西.平遥站/220kV.北母线"
]

# 是否使用默认节点（False则交互输入）
USE_DEFAULT_NODES = False


# ==================== 时间配置 ====================
# 默认日期范围
DEFAULT_START_DATE = "2026-02-01"
DEFAULT_END_DATE = "2026-02-28"

# 是否使用默认日期（False则交互输入）
USE_DEFAULT_DATES = False


# ==================== 运行模式 ====================
# 运行模式: 'interactive' 或 'auto'
RUN_MODE = 'interactive'  # interactive: 交互式, auto: 自动化

# 自动化模式下的默认选项
AUTO_MODE_OPTION = 2  # 1: 单日, 2: 日期范围, 3: 批量节点


# ==================== 其他配置 ====================
SLEEP_TIME = 1
RETRY_TIMES = 3
OUTPUT_DIR = "output"
