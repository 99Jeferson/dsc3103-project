# Observed data-quality issues

The raw market-price source (`data/raw/prices.csv`) contains issues handled by the validation and cleaning stages:

- Non-positive prices are rejected.
- Repeated IDs and exact duplicate rows are removed.
- Invalid dates are rejected.
- Missing or placeholder market values are imputed when a valid mode exists.
- Commodity labels with case or spelling variations are normalized and reviewed.

The current raw-data profile is summarized in `validation_report.md`; counts for different rules can overlap, so they should not be added together as unique affected rows. Rainfall may be missing for some market/date observations; the merge intentionally preserves those values as null rather than silently replacing them with zero.
