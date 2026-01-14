import joblib
import pandas as pd

from .config import MODEL_DIR, TIME_COL
from .dataloader import basic_cleaning
from .features import build_feature_dataset
from .utils import get_logger

logger = get_logger(__name__)


def load_trained_model(model_name: str = "dayahead_price_model.pkl"):
    model_path = MODEL_DIR / model_name
    logger.info(f"Loading model from {model_path}")
    bundle = joblib.load(model_path)
    return bundle["model"], bundle["feature_cols"]


def predict_for_dataframe(df: pd.DataFrame, model_name: str = "dayahead_price_model.pkl") -> pd.DataFrame:
    model, feature_cols = load_trained_model(model_name)

    df = basic_cleaning(df)
    df_feat = build_feature_dataset(df)

    X = df_feat[feature_cols]
    preds = model.predict(X)

    result = df_feat[[TIME_COL]].copy()
    result["pred_price"] = preds
    return result



