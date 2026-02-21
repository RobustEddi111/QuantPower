"""
配置文件示例
可以在这里预设常用的节点名称和日期范围
"""

# 常用节点列表
COMMON_NODES = [
    "华北.太钢/500kV.1母线",
    "华北.电网/500kV母线",
    # 添加更多节点...
]

# 默认日期范围
DEFAULT_START_DATE = "2026-02-01"
DEFAULT_END_DATE = "2026-02-28"

# 请求设置
REQUEST_TIMEOUT = 15  # 请求超时时间（秒）
RETRY_TIMES = 3  # 重试次数
SLEEP_TIME = 1  # 请求间隔（秒）

# 输出设置
OUTPUT_DIR = "./output"  # 输出目录
OUTPUT_FORMAT = "excel"  # 输出格式：excel 或 csv
