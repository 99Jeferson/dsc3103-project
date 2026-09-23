import pandas as pd


def rule_positive_price(df):
    """Return rows whose prices are not strictly positive."""
    invalid_prices = df[df["price"] <= 0].copy()
    invalid_prices["Reason"] = "Price must be greater than zero"
    return invalid_prices


def rule_duplicate_ids(df):
    """Return every row whose identifier is duplicated."""
    id_column = "record_id" if "record_id" in df.columns else "id"
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
    parsed_dates = pd.to_datetime(df["date"], errors="coerce", format="%Y-%m-%d")
    result = df.loc[parsed_dates.isna()].copy()
    result["Reason"] = "Invalid Date"
    return result


def rule_missing_market(df):
    """Return rows with missing market values."""
    missing_market = df[df["market"].isnull()].copy()
    missing_market["Reason"] = "Missing Market"
    return missing_market


def rule_known_commodity(df):
    """Return rows with non-canonical commodity spellings."""
    cleaned = df["commodity"].astype(str).str.strip()
    is_not_canonical = ~cleaned.isin(["Maize", "Beans"])
    result = df.loc[is_not_canonical].copy()
    result["Reason"] = "Inconsistent Commodity"
    return result.sort_values("commodity")

if __name__ == "__main__":
    from src.common.config import SOURCE_A_RAW_PATH

    prices = pd.read_csv(SOURCE_A_RAW_PATH)
    checks = {
        "positive_price": rule_positive_price(prices),
        "duplicate_ids": rule_duplicate_ids(prices),
        "duplicate_rows": rule_duplicate_rows(prices),
        "valid_date": rule_valid_date(prices),
        "missing_market": rule_missing_market(prices),
        "known_commodity": rule_known_commodity(prices),
    }
    print(f"Validated Source A: {len(prices)} rows")
    for name, failures in checks.items():
        print(f"{name}: {len(failures)} affected rows")