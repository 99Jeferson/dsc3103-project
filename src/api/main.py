import json
from datetime import date
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.common.features import feature_code_sha256, make_features

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "models" / "model.joblib"
META_PATH = ROOT / "models" / "model_metadata.json"

app = FastAPI(title="Market Price Prediction Service")

model = joblib.load(MODEL_PATH)
metadata = json.loads(META_PATH.read_text(encoding="utf-8"))


class PriceRequest(BaseModel):
    market: Literal[
        "Owino", "Nakasero", "Kalerwe", "Mbale Central", "Gulu Main", "Unknown"
    ]
    commodity: Literal["Maize", "Beans", "Cassava", "Rice"]
    date: date
    rainfall_mm: float = Field(ge=0, le=500)


@app.get("/health")
def health():
    feature_matches = feature_code_sha256() == metadata["feature_code_sha256"]
    return {
        "status": "ok" if feature_matches else "degraded",
        "model_version": metadata["model_version"],
        "model_type": metadata["model_type"],
        "feature_code_matches": feature_matches,
    }


@app.post("/predict")
def predict(request: PriceRequest):
    raw = pd.DataFrame([request.model_dump()])
    features = make_features(raw)[metadata["features"]]
    predicted_price = float(model.predict(features)[0])
    return {
        "predicted_price": round(predicted_price, 2),
        "model_version": metadata["model_version"],
    }
