import pandas as pd
from .config import TIME_COL
from .utils import get_logger



logger = get_logger(__name__)


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    if TIME_COL not in df.columns:
        raise ValueError(f"{TIME_COL} not in columns")

    df = df.copy()
    dt = pd.to_datetime(df[TIME_COL])

    df["hour"] = dt.dt.hour
    df["weekday"] = dt.dt.weekday
    df["is_weekend"] = df["weekday"].isin([5, 6]).astype(int)

    return df


def build_feature_dataset(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Building features...")
    df = add_time_features(df)
    # 之后可以在这里继续加气象、负荷等特征
    return df


