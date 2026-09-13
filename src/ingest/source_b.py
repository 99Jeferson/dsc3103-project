from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import SOURCE_B_RAW_PATH


def ingest_source_b(path: str | Path = SOURCE_B_RAW_PATH) -> pd.DataFrame:
    """Read the related rainfall file and validate the expected schema."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Source B file not found: {file_path}")

    df = pd.read_csv(file_path)
    required = {"market", "date", "rainfall_mm"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Expected columns {sorted(required)} but missing {sorted(missing)} in {file_path.name}")

    cleaned = df.copy()
    cleaned["market"] = cleaned["market"].astype(str).str.strip().str.casefold()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="raise").dt.strftime("%Y-%m-%d")
    cleaned["rainfall_mm"] = pd.to_numeric(cleaned["rainfall_mm"], errors="raise")
    return cleaned[["market", "date", "rainfall_mm"]].drop_duplicates().reset_index(drop=True)


def get_mkt_rainfall(mkt_name, latitude, longitude, start_date, end_date, timezone="auto", daily="precipitation_sum"):
    """Placeholder compatibility function for rainfall API access when configured."""
    raise NotImplementedError("Use ingest_source_b() for the local rainfall table in this project.")
