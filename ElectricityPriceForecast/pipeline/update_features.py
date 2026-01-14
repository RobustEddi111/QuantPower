"""
将 cleaned 数据转成特征表并保存到 data/features/

用法：
    python -m pipeline.update_features --cleaned cleaned_price_data.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.config import CLEANED_DATA_DIR, FEATURE_DATA_DIR  # noqa: E402
from src.features import build_feature_dataset  # noqa: E402
from src.utils import get_logger, ensure_dir  # noqa: E402

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Update feature dataset.")
    parser.add_argument(
        "--cleaned",
        type=str,
        required=True,
        help="位于 data/cleaned 下的文件名",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    cleaned_path = CLEANED_DATA_DIR / args.cleaned
    if not cleaned_path.exists():
        raise FileNotFoundError(cleaned_path)

    logger.info(f"Loading cleaned data from {cleaned_path}")
    df = pd.read_csv(cleaned_path)

    logger.info("Building features...")
    df_feat = build_feature_dataset(df)

    ensure_dir(FEATURE_DATA_DIR)
    output_path = FEATURE_DATA_DIR / f"feature_{args.cleaned}"
    df_feat.to_csv(output_path, index=False)

    logger.info(f"Feature dataset saved to {output_path}")


if __name__ == "__main__":
    main()
