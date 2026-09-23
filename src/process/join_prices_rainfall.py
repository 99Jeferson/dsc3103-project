import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

prices = pd.read_parquet(ROOT / "data/processed/prices_clean.parquet")

# Adjust this to your actual rainfall file and columns
rain = pd.read_csv(ROOT / "data/raw/rainfall.csv")

prices["date"] = pd.to_datetime(prices["date"], errors="coerce")
rain["date"] = pd.to_datetime(rain["date"], errors="coerce")

# Normalise names if needed
for col in ["market", "commodity"]:
    if col in prices.columns:
        prices[col] = prices[col].astype(str).str.strip()
    if col in rain.columns:
        rain[col] = rain[col].astype(str).str.strip()

# Typical join: market + date
joined = prices.merge(
    rain[["market", "date", "rainfall_mm"]],
    on=["market", "date"],
    how="left"
)

# Optional: fill rainfall missing values if required by your project rules
# joined["rainfall_mm"] = joined["rainfall_mm"].fillna(0)

joined = joined.sort_values(["date", "market", "commodity"]).reset_index(drop=True)

out_path = ROOT / "data/processed/prices_with_rainfall.parquet"
joined.to_parquet(out_path, index=False)

print(f"Saved joined dataset: {len(joined)} rows")
print(f"Output: {out_path}")

p = Path("data/processed/prices_with_rainfall.parquet")
df = pd.read_parquet(p)
print(df.shape)
print(df.isnull().sum())