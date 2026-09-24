"""Clean prices.csv using the shared validation rules and record every action."""

import sys
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from src.validate import rules

RAW_PATH = "data/raw/prices.csv"
OUTPUT_PATH = "data/processed/prices_clean.parquet"

def clean_data(
    df=None,
    path=RAW_PATH,
    output_path=OUTPUT_PATH,
    log_path="docs/cleaning_log.csv",
):
    if df is None:
        df = pd.read_csv(path)
    else:
        df = df.copy()
    log = []

    # 1. exact duplicate rows
    dup_rows = rules.rule_duplicate_rows(df)
    if not dup_rows.empty:
        df = df.drop_duplicates().copy()
        log.append({
            "rule": "rule_duplicate_rows",
            "action": "deduplicate",
            "rows_affected": len(dup_rows),
        })

    # 2. duplicate IDs
    if "id" in df.columns:
        dup_ids = rules.rule_duplicate_ids(df)
        if not dup_ids.empty:
            df = df.drop(index=dup_ids.index.drop_duplicates()).copy()
            log.append({
                "rule": "rule_duplicate_ids",
                "action": "reject",
                "rows_affected": len(dup_ids),
            })

    # 3. invalid prices
    bad_prices = rules.rule_positive_price(df)
    if not bad_prices.empty:
        df = df.drop(index=bad_prices.index)
        log.append({
            "rule": "rule_positive_price",
            "action": "reject",
            "rows_affected": len(bad_prices),
        })

    # 4. invalid dates
    bad_dates = rules.rule_valid_date(df)
    if not bad_dates.empty:
        df = df.drop(index=bad_dates.index)
        log.append({
            "rule": "rule_valid_date",
            "action": "reject",
            "rows_affected": len(bad_dates),
        })

    # 5. missing markets
    missing_markets = rules.rule_missing_market(df)
    if not missing_markets.empty:
        mode_market = df["market"].dropna().astype(str).str.strip().mode()
        if mode_market.empty:
            raise ValueError("every market value is missing; cannot impute market")
        df.loc[missing_markets.index, "market"] = mode_market.iloc[0]
        log.append({
            "rule": "missing_market",
            "action": "impute",
            "rows_affected": len(missing_markets),
        })

    # 6. commodity normalization
    if "commodity" in df.columns:
        df["commodity"] = (
            df["commodity"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.title()
            .replace({"Unknown": "Unknown", "Error": "Unknown"})
        )

        commodity_issues = rules.rule_known_commodity(df)
        if not commodity_issues.empty:
            # keep valid names, but flag unknowns for review
            log.append({
                "rule": "rule_known_commodity",
                "action": "review",
                "rows_affected": len(commodity_issues),
            })

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    if log_path is not None:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(log).to_csv(log_path, index=False)
    return df, log


if __name__ == "__main__":
    cleaned, decisions = clean_data()
    print(f"Wrote {len(cleaned)} rows to {OUTPUT_PATH}")
    for decision in decisions:
        print(f"{decision['rule']}: {decision['action']} ({decision['rows_affected']} rows)")
