"""
每日 D+1 电价预测流水线（示例）

用法：
    python -m pipeline.run_d1_forecast --date 2025-01-03
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.config import DATA_DIR, TIME_COL  # noqa: E402
from src.model_predict import predict_for_dataframe  # noqa: E402
from src.utils import get_logger, ensure_dir  # noqa: E402

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Run D+1 dayahead price forecast.")
    parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="预测日期，如 2025-01-03",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    target_date = datetime.strptime(args.date, "%Y-%m-%d").date()

    logger.info(f"Start D+1 forecast for date = {target_date}")

    raw_dir = DATA_DIR / "raw"
    ensure_dir(raw_dir)

    input_csv = raw_dir / f"d1_input_{target_date.strftime('%Y%m%d')}.csv"
    if not input_csv.exists():
        logger.error(f"Input file not found: {input_csv}")
        return

    df_input = pd.read_csv(input_csv, parse_dates=[TIME_COL])

    df_pred = predict_for_dataframe(df_input)

    output_dir = DATA_DIR / "features" / "predictions"
    ensure_dir(output_dir)
    output_file = output_dir / f"pred_dayahead_{target_date.strftime('%Y%m%d')}.csv"
    df_pred.to_csv(output_file, index=False)

    logger.info(f"Prediction saved to: {output_file}")


if __name__ == "__main__":
    main()
