"""Clean prices.csv using the shared validation rules and record every action."""

from hashlib import sha256
from pathlib import Path

import pandas as pd

from src.validate import rules

ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "prices.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "prices_clean.parquet"
LOG_PATH = ROOT / "docs" / "cleaning_log.csv"


def file_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_data(path: Path = RAW_PATH, output_path: Path = OUTPUT_PATH) -> tuple[pd.DataFrame, list[dict]]:
    """Clean the raw file and return the cleaned frame plus an action log."""
    before_hash = file_hash(path)
    df = pd.read_csv(path)
    log = []

    duplicate_rows = rules.rule_duplicate_rows(df)
    duplicate_row_indices = set(df.index[df.duplicated(keep="first")])
    if duplicate_row_indices:
        df = df.drop(index=duplicate_row_indices)
        log.append({"rule": "duplicate_rows", "action": "reject", "rows_affected": len(duplicate_row_indices), "reason": "Removed repeated exact records; retained the first copy."})

    id_column = "record_id" if "record_id" in df.columns else "id"
    duplicate_ids = rules.rule_duplicate_ids(df)
    duplicate_id_indices = set(df.index[df[id_column].duplicated(keep="first")])
    if duplicate_id_indices:
        df = df.drop(index=duplicate_id_indices)
        log.append({"rule": "duplicate_ids", "action": "reject", "rows_affected": len(duplicate_id_indices), "reason": f"Removed later records sharing a {id_column}."})

    invalid_prices = rules.rule_positive_price(df)
    if not invalid_prices.empty:
        df = df.drop(index=invalid_prices.index)
        log.append({"rule": "positive_price", "action": "reject", "rows_affected": len(invalid_prices), "reason": "A price must be greater than zero."})

    invalid_dates = rules.rule_valid_date(df)
    if not invalid_dates.empty:
        df = df.drop(index=invalid_dates.index)
        log.append({"rule": "valid_date", "action": "reject", "rows_affected": len(invalid_dates), "reason": "The date must be a real YYYY-MM-DD date."})

    missing_market = rules.rule_missing_market(df)
    if not missing_market.empty:
        market_mode = df["market"].dropna().mode().iloc[0]
        df.loc[missing_market.index, "market"] = market_mode
        log.append({"rule": "missing_market", "action": "impute", "rows_affected": len(missing_market), "reason": f"Filled missing markets with the mode: {market_mode}."})

    inconsistent_commodities = rules.rule_known_commodity(df)
    if not inconsistent_commodities.empty:
        df["commodity"] = df["commodity"].astype(str).str.strip().str.casefold().map({"maize": "Maize", "beans": "Beans"})
        log.append({"rule": "known_commodity", "action": "normalize", "rows_affected": len(inconsistent_commodities), "reason": "Mapped case and whitespace variants to Maize or Beans."})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    after_hash = file_hash(path)
    if before_hash != after_hash:
        raise RuntimeError("Raw file hash changed during cleaning.")
    log.append({"rule": "raw_file_hash", "action": "verify", "rows_affected": 0, "reason": f"Unchanged SHA-256: {after_hash}"})
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(log).to_csv(LOG_PATH, index=False)
    return df, log


if __name__ == "__main__":
    cleaned, decisions = clean_data()
    print(f"Wrote {len(cleaned)} rows to {OUTPUT_PATH}")
    for decision in decisions:
        print(f"{decision['rule']}: {decision['action']} ({decision['rows_affected']} rows)")
