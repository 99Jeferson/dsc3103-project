"""Merge cleaned market prices with rainfall observations."""

import pandas as pd


def merge_prices_with_rainfall(
	prices: pd.DataFrame,
	rainfall: pd.DataFrame,
) -> pd.DataFrame:
	"""Left-join prices and rainfall by normalized market and date.

	A left join keeps every cleaned price record. Rainfall remains missing when
	no observation exists for a particular market/date combination.
	"""
	required_price_columns = {"market", "date"}
	required_rainfall_columns = {"market", "date", "rainfall_mm"}

	missing_price_columns = required_price_columns - set(prices.columns)
	missing_rainfall_columns = required_rainfall_columns - set(rainfall.columns)
	if missing_price_columns:
		raise ValueError(f"Prices missing required columns: {sorted(missing_price_columns)}")
	if missing_rainfall_columns:
		raise ValueError(
			f"Rainfall missing required columns: {sorted(missing_rainfall_columns)}"
		)

	prices = prices.copy()
	rainfall = rainfall.copy()

	for frame in (prices, rainfall):
		frame["market"] = frame["market"].astype(str).str.strip().str.casefold()
		frame["date"] = pd.to_datetime(frame["date"], errors="coerce").dt.strftime(
			"%Y-%m-%d"
		)

	rainfall = rainfall[["market", "date", "rainfall_mm"]]
	return prices.merge(rainfall, how="left", on=["market", "date"])
