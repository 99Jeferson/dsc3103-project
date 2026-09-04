import pandas as pd


def rule_positive_price(df):
    """Return rows with negative prices."""
    neg_prices = df[df["price"] < 0].copy()
    neg_prices["Reason"] = "Negative Price"
    return neg_prices


def rule_duplicate_ids(df):
    """Return rows with duplicate id values."""
    duplicate_id = df["id"].duplicated(keep=False)
    duplicates = df[duplicate_id].copy()
    duplicates["Reason"] = "Duplicate ID"
    return duplicates.sort_values("id")


def rule_duplicate_rows(df):
    """Return exact duplicate rows (all columns identical)."""
    duplicate_rows = df.duplicated(keep=False)
    duplicates = df[duplicate_rows].copy()
    duplicates["Reason"] = "Duplicate Row"
    return duplicates.sort_values(list(df.columns))


def rule_valid_date(df):
    """Return rows with invalid dates."""
    invalid_dates = []
    for idx, row in df.iterrows():
        try:
            date_str = str(row["date"]).strip()
            parts = date_str.split("-")
            if len(parts) != 3:
                invalid_dates.append(idx)
                continue
            year, month, day = map(int, parts)
            if month < 1 or month > 12 or day < 1 or day > 31:
                invalid_dates.append(idx)
        except (TypeError, ValueError):
            invalid_dates.append(idx)

    result = df.loc[invalid_dates].copy()
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