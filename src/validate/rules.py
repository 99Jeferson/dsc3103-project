import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

VALID_COMMODITIES = {"Maize", "Beans"}


def rule_positive_price(df):
    """Return rows whose prices are not strictly positive."""
    if "price" not in df.columns:
        return df.iloc[0:0].copy()

    price_numeric = pd.to_numeric(df["price"], errors="coerce")
    invalid_prices = df.loc[price_numeric <= 0].copy()
    invalid_prices["Reason"] = "Price must be greater than zero"
    return invalid_prices


def rule_duplicate_ids(df):
    """Return every row whose identifier is duplicated."""
    id_column = "record_id" if "record_id" in df.columns else "id"
    if id_column not in df.columns:
        return df.iloc[0:0].copy()

    duplicate_id = df[id_column].duplicated(keep=False)
    duplicates = df[duplicate_id].copy()
    duplicates["Reason"] = "Duplicate ID"
    return duplicates.sort_values(id_column)


def rule_duplicate_rows(df):
    """Return exact duplicate rows (all columns identical)."""
    duplicate_rows = df.duplicated(keep=False)
    duplicates = df[duplicate_rows].copy()
    duplicates["Reason"] = "Duplicate Row"
    return duplicates.sort_values(list(df.columns))


def rule_valid_date(df):
    """Return rows with invalid dates."""
    if "date" not in df.columns:
        return df.iloc[0:0].copy()

    parsed_dates = pd.to_datetime(df["date"], errors="coerce", format="%Y-%m-%d")
    result = df.loc[parsed_dates.isna()].copy()
    result["Reason"] = "Invalid Date"
    return result


def rule_missing_market(df):
    """Return rows with missing market values."""
    if "market" not in df.columns:
        return df.iloc[0:0].copy()

    market_clean = df["market"].fillna("").astype(str).str.strip()
    missing_market = df.loc[
        market_clean.eq("") | market_clean.isin(["UNKNOWN", "ERROR", "NULL", "N/A"])
    ].copy()
    missing_market["Reason"] = "Missing Market"
    return missing_market


def rule_known_commodity(df):
    """Return rows with commodity issues using actual dirty CSV values."""
    if "commodity" not in df.columns:
        return df.iloc[0:0].copy()

    values = df["commodity"].fillna("").astype(str).str.strip()
    issues = []

    for idx, raw in values.items():
        value = raw.strip()

        if value == "":
            issues.append((idx, "Unknown Commodity", None))
            continue

        canonical = value.title()

        if canonical in VALID_COMMODITIES:
            if canonical != value:
                issues.append((idx, "Commodity formatting mismatch", canonical))
            continue

        if value.upper() in {"UNKNOWN", "ERROR", "NULL", "N/A"}:
            issues.append((idx, "Unknown Commodity", None))
            continue

        issues.append((idx, "Unknown Commodity", None))

    if not issues:
        return df.iloc[0:0].copy()

    issue_df = pd.DataFrame(issues, columns=["index", "Reason", "Suggested Value"])
    out = df.loc[issue_df["index"]].copy()
    out["Reason"] = issue_df["Reason"].values
    out["Suggested Value"] = issue_df["Suggested Value"].values
    return out.sort_values("commodity")


def rule_negative_rain(df):
    """Return rows where rainfall is negative."""
    if "rainfall_mm" not in df.columns:
        return df.iloc[0:0].copy()

    rain_numeric = pd.to_numeric(df["rainfall_mm"], errors="coerce")
    invalid_rain = df.loc[rain_numeric < 0].copy()
    invalid_rain["Reason"] = "Rainfall cannot be negative"
    return invalid_rain


if __name__ == "__main__":
    from pathlib import Path

    parquet_path = Path("data/processed/prices_clean.parquet")
    if not parquet_path.exists():
        raise FileNotFoundError(f"Missing cleaned parquet: {parquet_path}")

    df = pd.read_parquet(parquet_path)

    checks = {
        "positive_price": rule_positive_price(df),
        "duplicate_ids": rule_duplicate_ids(df),
        "duplicate_rows": rule_duplicate_rows(df),
        "valid_date": rule_valid_date(df),
        "missing_market": rule_missing_market(df),
        "known_commodity": rule_known_commodity(df),
        "negative_rain": rule_negative_rain(df),
    }

    for name, result in checks.items():
        print(f"{name}: {len(result)}")

    total_issues = sum(len(v) for v in checks.values())
    print(f"total_issues: {total_issues}")