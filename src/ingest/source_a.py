from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.common.config import SOURCE_A_RAW_PATH


def ingest_source_a(path: str | Path = SOURCE_A_RAW_PATH) -> pd.DataFrame:
    """Read the raw prices table and validate the expected schema."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Source A file not found: {file_path}")

    df = pd.read_csv(file_path)
    required = {"id", "date", "market", "commodity", "price"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Source A schema mismatch: missing columns {sorted(missing)}")
    return df.copy()


if __name__ == "__main__":
    prices = ingest_source_a()
    print(f"Source A loaded: {len(prices)} rows")
    print(f"Columns: {', '.join(prices.columns)}")
    print(f"Input: {SOURCE_A_RAW_PATH}")