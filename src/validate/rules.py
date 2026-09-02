def rule_positive_price(df):
    """Return rows with negative prices."""
    neg_prices = df[df["price"] < 0].copy()
    neg_prices["Reason"] = "Negative Price"
    return neg_prices


def rule_duplicate_ids(df):
    """Return rows with duplicate id values."""
    duplicate_id_mask = df["id"].duplicated(keep=False)
    duplicates = df[duplicate_id_mask].copy()
    duplicates["Reason"] = "Duplicate ID"
    return duplicates.sort_values("id")


def rule_duplicate_rows(df):
    """Return exact duplicate rows (all columns identical)."""
    duplicate_row_mask = df.duplicated(keep=False)
    duplicates = df[duplicate_row_mask].copy()
    duplicates["Reason"] = "Duplicate Row"
    return duplicates.sort_values(list(df.columns))


def rule_valid_date(df):
    """Return rows with invalid dates."""
    invalid_dates = []
    invalid_rows = df.copy()
    
    for idx, row in df.iterrows():
        try:
            # Check for impossible month values (>12)
            date_str = row["date"]
            parts = str(date_str).split("-")
            if len(parts) == 3:
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                if month > 12 or month < 1 or day > 31 or day < 1:
                    invalid_dates.append(idx)
        except (ValueError, TypeError):
            invalid_dates.append(idx)
    
    result = df.iloc[invalid_dates].copy()
    result["Reason"] = "Invalid Date"
    return result


def rule_missing_market(df):
    """Return rows with missing market values."""
    missing_market = df[df["market"].isnull()].copy()
    missing_market["Reason"] = "Missing Market"
    return missing_market


def rule_known_commodity(df):
    """Return rows with non-canonical commodity spellings."""
    # Define the canonical forms (most common from the dataset)
    canonical_forms = {
        "maize": "MAIZE",
        "beans": "BEANS",
    }
    
    # Rows that are NOT in the most common forms (MAIZE or BEANS)
    is_not_canonical = ~df["commodity"].isin(["MAIZE", "BEANS"])
    result = df[is_not_canonical].copy()
    result["Reason"] = "Inconsistent Commodity"
    return result
