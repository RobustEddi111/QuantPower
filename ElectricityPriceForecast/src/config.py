from pathlib import Path


# 项目根目录：.../QuantPower/ElectricityPriceForecast
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CLEANED_DATA_DIR = DATA_DIR / "cleaned"
FEATURE_DATA_DIR = DATA_DIR / "features"

# 模型目录（先用日前）
MODEL_DIR = PROJECT_ROOT / "models" / "dayahead"

# 列名配置
TIME_COL = "time"
TARGET_COL = "price"

# 默认特征列（在 features.py 中生成）
DEFAULT_FEATURE_COLS = ["hour", "weekday", "is_weekend"]
