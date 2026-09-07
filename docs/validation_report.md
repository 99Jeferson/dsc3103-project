# Validation Report

## Raw-file profile
- Rows: 1010
- Exact duplicate rows: 10
- Rows with duplicate IDs: 53
- Distinct duplicated ID values: 26

### Inferred schema

| Column | Inferred type | Missing values |
|---|---|---:|
| id | `int64` | 0 |
| date | `str` | 0 |
| market | `str` | 189 |
| commodity | `str` | 0 |
| price | `int64` | 0 |

### Rule results and actions

| Rule | Failed rows | Action |
|---|---:|---|
| `positive_price` | 54 | Reject rows with price <= 0 |
| `duplicate_ids` | 53 | Reject repeated record identifiers |
| `duplicate_rows` | 20 | Reject exact duplicate rows |
| `valid_date` | 29 | Reject rows with invalid dates |
| `missing_market` | 189 | Impute the market with the mode |
| `known_commodity` | 516 | Normalize commodity spelling/case |

### Inconsistent categories

Normalized commodity groups found: beans, maize.

### Numeric summary

| Column | Mean | Median | Min | Max | Std |
|---|---:|---:|---:|---:|---:|
| id | 494.78 | 494.50 | 0.00 | 999.00 | 291.21 |
| price | 366.34 | 500.00 | -2000.00 | 500.00 | 562.68 |
