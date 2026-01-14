import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit

from .config import TARGET_COL, DEFAULT_FEATURE_COLS, MODEL_DIR
from .dataloader import load_cleaned_data
from .features import build_feature_dataset
from .metrics import evaluate
from .utils import ensure_dir, get_logger

logger = get_logger(__name__)


def train_day_ahead_model(
    cleaned_filename: str,
    model_name: str = "dayahead_price_model.pkl",
):
    # 1. 读取清洗数据
    df = load_cleaned_data(cleaned_filename)

    # 2. 特征工程
    df_feat = build_feature_dataset(df)

    X = df_feat[DEFAULT_FEATURE_COLS]
    y = df_feat[TARGET_COL]

    # 3. 简单时间序列交叉验证
    tscv = TimeSeriesSplit(n_splits=3)
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X), start=1):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=10,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        metrics = evaluate(y_val.values, y_pred)
        logger.info(f"Fold {fold} metrics: {metrics}")

    # 4. 用全部数据重训最终模型
    final_model = RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        random_state=42,
        n_jobs=-1,
    )
    final_model.fit(X, y)

    # 5. 保存模型
    ensure_dir(MODEL_DIR)
    model_path = MODEL_DIR / model_name
    joblib.dump({"model": final_model, "feature_cols": DEFAULT_FEATURE_COLS}, model_path)
    logger.info(f"Model saved to {model_path}")


if __name__ == "__main__":
    # 对应 data/cleaned/cleaned_price_data.csv
    train_day_ahead_model("cleaned_price_data.csv")
