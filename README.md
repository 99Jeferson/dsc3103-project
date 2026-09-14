# DSC3103 Project

This repository contains the DSC3103 Lab 3 ETL pipeline for cleaning market prices,
joining them to rainfall observations, and writing a reproducible Parquet output.

## Project structure

```
dsc3103-project/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── src/
│   ├── ingest/       # Source A prices and Source B rainfall readers
│   ├── validate/     # Reusable quality rules and profiling
│   ├── transform/    # Cleaning and action logging
│   ├── common/       # Paths, environment settings, and logging helpers
│   └── run_pipeline.py  # Single pipeline entry point
├── tests/
├── notebooks/
└── docs/
```

## Run the pipeline

From the repository root, run the single documented entry point:

	python -m src.run_pipeline

The pipeline reads `data/raw/prices.csv` and `data/raw/rainfall.csv`, validates
their schemas, cleans invalid price records and categories, imputes missing
markets, joins both sources on `market` and `date`, and overwrites these outputs:

- `data/processed/prices_clean.parquet`
- `data/processed/market_prices_with_rainfall.parquet`
- `docs/cleaning_log.csv`
- `docs/pipeline_log.json`
- `docs/pipeline.log` (human-readable runtime messages)

Overwrite semantics make repeated runs idempotent: rerunning the command rebuilds
the outputs from the raw inputs without appending duplicate rows.

## Data

The raw dataset is stored in `data/raw/dirty_cafe_sales.csv` and has been left unmodified as received.

## Tests

Run the fast unit tests with:

	python -m pytest -q

## Notes

- `docs/data_source.md`: describes the dataset type, variables, and target/feature candidates.
- `docs/issues_observed.md`: records suspicious values observed during the initial inspection.
- `notebooks/01_inspection.ipynb`: loads the raw file and runs only inspection operations.
