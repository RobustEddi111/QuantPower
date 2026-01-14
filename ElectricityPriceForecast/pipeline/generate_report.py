"""
根据预测结果和实际结果，输出一个简单日报（指标写到 .txt）

用法：
    python -m pipeline.generate_report \
        --pred data/features/predictions/pred_dayahead_20250103.csv \
        --actual data/cleaned/actual_price_20250103.csv
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.config import TIME_COL, TARGET_COL  # noqa: E402
from src.metrics import evaluate  # noqa: E402
from src.utils import get_logger  # noqa: E402

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate daily forecast report.")
    parser.add_argument("--pred", type=str, required=True, help="预测结果 CSV 路径")
    parser.add_argument("--actual", type=str, required=True, help="实际电价 CSV 路径")
    return parser.parse_args()


def main():
    args = parse_args()

    pred_path = Path(args.pred)
    actual_path = Path(args.actual)

    if not pred_path.exists():
        raise FileNotFoundError(pred_path)
    if not actual_path.exists():
        raise FileNotFoundError(actual_path)

    df_pred = pd.read_csv(pred_path, parse_dates=[TIME_COL])
    df_actual = pd.read_csv(actual_path, parse_dates=[TIME_COL])

    df = pd.merge(
        df_pred[[TIME_COL, "pred_price"]],
        df_actual[[TIME_COL, TARGET_COL]],
        on=TIME_COL,
        how="inner",
    )

    metrics = evaluate(df[TARGET_COL].values, df["pred_price"].values)
    logger.info(f"Daily metrics: {metrics}")

    report_path = pred_path.with_suffix(".report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Forecast Report for {pred_path.name}\n")
        f.write(f"Samples: {len(df)}\n")
        for k, v in metrics.items():
            f.write(f"{k}: {metrics[k]:.4f}\n")

    logger.info(f"Report saved to {report_path}")


if __name__ == "__main__":
    main()
