import hashlib
import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LinearRegression

from src.common.features import feature_code_sha256, make_features

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "prices_with_rainfall.parquet"
MODEL_PATH = ROOT / "models" / "model.joblib"
META_PATH = ROOT / "models" / "model_metadata.json"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def train():
    df = pd.read_parquet(DATA_PATH).dropna(subset=["price"])
    X = make_features(df)
    y = df["price"]

    model = LinearRegression().fit(X, y)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    metadata = {
        "model_version": datetime.now().strftime("%Y%m%d-%H%M%S"),
        "model_type": "LinearRegression",
        "features": list(X.columns),
        "n_training_rows": len(df),
        "training_data_path": str(DATA_PATH.relative_to(ROOT)),
        "training_data_sha256": file_sha256(DATA_PATH),
        "feature_code_sha256": feature_code_sha256(),
        "train_r2": round(model.score(X, y), 4),
    }
    META_PATH.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print("Saved", MODEL_PATH.relative_to(ROOT), "and", META_PATH.relative_to(ROOT))
    print(metadata["model_version"], "R2 =", metadata["train_r2"])


if __name__ == "__main__":
    train()
