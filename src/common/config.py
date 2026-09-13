from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

SOURCE_A_RAW_PATH = BASE_DIR / "data" / "raw" / "prices.csv"
SOURCE_B_RAW_PATH = BASE_DIR / "data" / "raw" / "rainfall.csv"
PROCESSED_PATH = BASE_DIR / "data" / "processed" / "prices_clean.parquet"
FINAL_PROCESSED_PATH = BASE_DIR / "data" / "processed" / "market_prices_with_rainfall.parquet"
PIPELINE_LOG_PATH = BASE_DIR / "docs" / "pipeline_log.json"
CLEANING_LOG_PATH = BASE_DIR / "docs" / "cleaning_log.csv"

MARKET_COORDS = {"mukono": (0.3533, 32.7556), "bwais": (0.3475, 32.5761), "nakasero": (0.3136, 32.5825), "kansanga": (0.2833, 32.6000)}

RAINFALL_START_DATE = os.getenv("RAINFALL_START_DATE", "2020-01-01")
RAINFALL_END_DATE = os.getenv("RAINFALL_END_DATE", "2022-06-30")
RAINFALL_URL = os.getenv("RAINFALL_URL", "")

MIN_PRICE = float(os.getenv("MIN_PRICE", "0"))
PRICE_RULE_SEVERITY = os.getenv("PRICE_RULE_SEVERITY", "quarantine")

__all__ = [
    "BASE_DIR",
    "SOURCE_A_RAW_PATH",
    "SOURCE_B_RAW_PATH",
    "PROCESSED_PATH",
    "FINAL_PROCESSED_PATH",
    "PIPELINE_LOG_PATH",
    "CLEANING_LOG_PATH",
    "MARKET_COORDS",
    "RAINFALL_START_DATE",
    "RAINFALL_END_DATE",
    "RAINFALL_URL",
    "MIN_PRICE",
    "PRICE_RULE_SEVERITY",
]