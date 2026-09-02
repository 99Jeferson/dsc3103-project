import pandas as pd
from src.validate.rules import (
    rule_positive_price,
    rule_duplicate_ids,
    rule_duplicate_rows,
    rule_valid_date,
    rule_missing_market,
    rule_known_commodity,
)

# Load the dataset
df = pd.read_csv("data/raw/prices.csv")

print("=" * 70)
print("DATA QUALITY VALIDATION CHECKS")
print("=" * 70)
print(f"\nTotal rows in dataset: {len(df)}\n")

# Rule 1: Positive Price
print("RULE 1: Positive Price")
print("-" * 70)
neg_prices = rule_positive_price(df)
print(f"Rows with negative prices: {len(neg_prices)}")
if len(neg_prices) > 0:
    print(neg_prices[["id", "price", "Reason"]].head(10))
print()

# Rule 2: Duplicate IDs
print("RULE 2: Duplicate IDs")
print("-" * 70)
dup_ids = rule_duplicate_ids(df)
print(f"Rows with duplicate IDs: {len(dup_ids)}")
if len(dup_ids) > 0:
    print(dup_ids[["id", "date", "market", "Reason"]].head(10))
print()

# Rule 3: Duplicate Rows
print("RULE 3: Duplicate Rows")
print("-" * 70)
dup_rows = rule_duplicate_rows(df)
print(f"Exact duplicate rows: {len(dup_rows)}")
if len(dup_rows) > 0:
    print(dup_rows[["id", "date", "market", "commodity", "price", "Reason"]].head(10))
print()

# Rule 4: Valid Date
print("RULE 4: Valid Date")
print("-" * 70)
invalid_dates = rule_valid_date(df)
print(f"Rows with invalid dates: {len(invalid_dates)}")
if len(invalid_dates) > 0:
    print(invalid_dates[["id", "date", "Reason"]].head(10))
print()

# Rule 5: Missing Market
print("RULE 5: Missing Market")
print("-" * 70)
missing_mkt = rule_missing_market(df)
print(f"Rows with missing market: {len(missing_mkt)}")
if len(missing_mkt) > 0:
    print(missing_mkt[["id", "market", "commodity", "Reason"]].head(10))
print()

# Rule 6: Known Commodity
print("RULE 6: Known Commodity (Inconsistent Spellings)")
print("-" * 70)
bad_commodity = rule_known_commodity(df)
print(f"Rows with inconsistent commodity spelling: {len(bad_commodity)}")
if len(bad_commodity) > 0:
    print(bad_commodity[["id", "commodity", "Reason"]].head(10))
print()

print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Negative/Zero Prices: {len(neg_prices)}")
print(f"Duplicate IDs: {len(dup_ids)}")
print(f"Duplicate Rows: {len(dup_rows)}")
print(f"Invalid Dates: {len(invalid_dates)}")
print(f"Missing Market: {len(missing_mkt)}")
print(f"Inconsistent Commodity: {len(bad_commodity)}")
print(f"Total quality issues: {len(neg_prices) + len(dup_ids) + len(dup_rows) + len(invalid_dates) + len(missing_mkt) + len(bad_commodity)}")
print("=" * 70)
