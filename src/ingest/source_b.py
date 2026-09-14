from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import urlopen
from pathlib import Path

import pandas as pd

from src.common.config import (
    MARKET_COORDS,
    RAINFALL_END_DATE,
    RAINFALL_SOURCE,
    RAINFALL_START_DATE,
    RAINFALL_TIMEZONE,
    RAINFALL_URL,
    SOURCE_B_RAW_PATH,
)


def _clean_rainfall_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize the common Source B table contract."""
    required = {"market", "date", "rainfall_mm"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Expected columns {sorted(required)} but missing {sorted(missing)}")

    cleaned = df.copy()
    cleaned["market"] = cleaned["market"].astype(str).str.strip().str.casefold()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="raise").dt.strftime("%Y-%m-%d")
    cleaned["rainfall_mm"] = pd.to_numeric(cleaned["rainfall_mm"], errors="raise")
    return cleaned[["market", "date", "rainfall_mm"]].drop_duplicates().reset_index(drop=True)


def _read_cached_rainfall(path: str | Path) -> pd.DataFrame:
    """Read a cached Source B CSV for explicit offline runs."""
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Source B file not found: {file_path}")

    return _clean_rainfall_frame(pd.read_csv(file_path))


def get_mkt_rainfall(mkt_name, latitude, longitude, start_date, end_date, timezone=RAINFALL_TIMEZONE, daily="precipitation_sum"):
    """Fetch daily rainfall for one market from the Open-Meteo archive API."""
    if not RAINFALL_URL:
        raise ValueError("RAINFALL_URL is empty; configure the Open-Meteo archive endpoint.")

    query = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": daily,
            "timezone": timezone,
        }
    )
    request_url = f"{RAINFALL_URL}?{query}"
    try:
        with urlopen(request_url, timeout=30) as response:
            payload = json.load(response)
    except Exception as exc:
        raise RuntimeError(f"Rainfall API request failed for {mkt_name}: {exc}") from exc

    if payload.get("error"):
        raise RuntimeError(f"Rainfall API returned an error for {mkt_name}: {payload.get('reason', 'unknown error')}")

    daily_data = payload.get("daily", {})
    dates = daily_data.get("time", [])
    rainfall = daily_data.get(daily, [])
    if len(dates) != len(rainfall):
        raise ValueError(f"Rainfall API returned mismatched date and rainfall lengths for {mkt_name}")

    return pd.DataFrame({"market": mkt_name, "date": dates, "rainfall_mm": rainfall})


def ingest_source_b(path: str | Path | None = None, *, use_api: bool | None = None) -> pd.DataFrame:
    """Fetch Source B from Open-Meteo, or read a CSV when explicitly requested.

    The API result is cached to ``SOURCE_B_RAW_PATH`` for reproducible offline use.
    Passing ``path`` always selects the CSV cache and is useful for tests.
    """
    if path is not None:
        return _read_cached_rainfall(path)

    fetch_from_api = use_api if use_api is not None else RAINFALL_SOURCE.casefold() == "api"
    if not fetch_from_api:
        return _read_cached_rainfall(SOURCE_B_RAW_PATH)

    frames = [
        get_mkt_rainfall(
            market,
            latitude,
            longitude,
            RAINFALL_START_DATE,
            RAINFALL_END_DATE,
        )
        for market, (latitude, longitude) in MARKET_COORDS.items()
    ]
    rainfall = _clean_rainfall_frame(pd.concat(frames, ignore_index=True))
    SOURCE_B_RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    rainfall.to_csv(SOURCE_B_RAW_PATH, index=False)
    return rainfall


if __name__ == "__main__":
    rainfall = ingest_source_b()
    print(f"Source B loaded from Open-Meteo: {len(rainfall)} rows")
    print(f"Markets: {', '.join(sorted(rainfall['market'].unique()))}")
    print(f"Date range: {rainfall['date'].min()} to {rainfall['date'].max()}")
    print(f"Cached at: {SOURCE_B_RAW_PATH}")


