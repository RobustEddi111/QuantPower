from pathlib import Path
import pandas as pd

from .config import RAW_DATA_DIR, CLEANED_DATA_DIR, TIME_COL
from .utils import get_logger, ensure_dir

logger = get_logger(__name__)


def load_raw_csv(filename: str) -> pd.DataFrame:
    path = RAW_DATA_DIR / filename
    logger.info(f"Loading raw data from {path}")
    return pd.read_csv(path)


def save_cleaned_data(df: pd.DataFrame, filename: str):
    ensure_dir(CLEANED_DATA_DIR)
    path = CLEANED_DATA_DIR / filename
    logger.info(f"Saving cleaned data to {path}")
    df.to_csv(path, index=False)


def load_cleaned_data(filename: str) -> pd.DataFrame:
    path = CLEANED_DATA_DIR / filename
    logger.info(f"Loading cleaned data from {path}")
    df = pd.read_csv(path, parse_dates=[TIME_COL])
    return df


def basic_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """简单清洗：按时间排序、去掉全空行"""
    if TIME_COL in df.columns:
        df[TIME_COL] = pd.to_datetime(df[TIME_COL])
        df = df.sort_values(TIME_COL)

    df = df.dropna(how="all").reset_index(drop=True)
    return df
