# Data sources

## Market prices (Source A)

The active raw source is `data/raw/prices.csv`, a structured CSV with one market-price observation per row. Its columns are `id`, `date`, `market`, `commodity`, and `price`. The ETL pipeline validates and cleans these records before joining them to rainfall.

## Rainfall (Source B)

The pipeline obtains daily rainfall from the Open-Meteo Historical Weather API for configured markets. It caches the result in `data/raw/rainfall.csv`, with columns `market`, `date`, and `rainfall_mm`. Set `RAINFALL_SOURCE=csv` to reuse that cache offline.

## Lab 4 assignment input

The assignment supplies `prices_with_rainfall.parquet`; place it at `data/processed/prices_with_rainfall.parquet`. It has columns `id`, `date`, `market`, `commodity`, `price`, and `rainfall_mm`. This is the input for `src/analytics/build_analytics.py`. It is distinct from the Lab 3 pipeline output `market_prices_with_rainfall.parquet`.
