import hashlib
from pathlib import Path

import pandas as pd

KNOWN_MARKETS = ["Owino", "Nakasero", "Kalerwe", "Mbale Central", "Gulu Main", "Unknown"]
KNOWN_COMMODITIES = ["Maize", "Beans", "Cassava", "Rice"]


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create the fixed, shared feature contract for training and serving."""
    out = pd.DataFrame(index=df.index)
    out["rainfall_mm"] = df["rainfall_mm"].fillna(0.0)
    out["month"] = pd.to_datetime(df["date"]).dt.month

    for market in KNOWN_MARKETS:
        out[f"market_{market}"] = (df["market"] == market).astype(int)
    for commodity in KNOWN_COMMODITIES:
        out[f"commodity_{commodity}"] = (df["commodity"] == commodity).astype(int)

    return out


def feature_code_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
