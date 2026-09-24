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

The pipeline reads `data/raw/prices.csv` and fetches Source B from the Open-Meteo
Historical Weather API. The API response is cached as `data/raw/rainfall.csv`.
The pipeline validates both sources, cleans invalid price records and categories,
imputes missing markets, joins both sources on `market` and `date`, and overwrites
these outputs:

- `data/processed/prices_clean.parquet`
- `data/processed/market_prices_with_rainfall.parquet`
- `docs/cleaning_log.csv`
- `docs/pipeline_log.json`
- `docs/pipeline.log` (human-readable runtime messages)

Overwrite semantics make repeated runs idempotent: rerunning the command rebuilds
the outputs from the raw inputs without appending duplicate rows.

The rainfall API is configured through `RAINFALL_URL`, `RAINFALL_START_DATE`,
`RAINFALL_END_DATE`, and `RAINFALL_TIMEZONE`. Set `RAINFALL_SOURCE=csv` to run
offline from the cached rainfall file instead.

## Inspect Parquet outputs

Parquet is a binary columnar data format, so the files are not meant to be
opened in VS Code's text editor. The message saying that the file is binary is
normal and does not indicate that the file is broken.

Use pandas to inspect a Parquet file as a table from the repository root:

```python
import pandas as pd

path = "data/processed/market_prices_with_rainfall.parquet"
df = pd.read_parquet(path)
print(df.shape)
print(df.dtypes)
print(df.head(10))
```

The same commands can be run in a notebook, or in a Python file with:

```text
python -c "import pandas as pd; print(pd.read_parquet('data/processed/market_prices_with_rainfall.parquet').head())"
```

The generated files are:

- `prices_clean.parquet`: cleaned prices before the rainfall join.
- `market_prices_with_rainfall.parquet`: the pipeline's final joined output.
- `prices_with_rainfall.parquet`: output from the standalone join script.

If a spreadsheet or text editor is required, convert a copy rather than
changing the pipeline output:

```python
pd.read_parquet("data/processed/market_prices_with_rainfall.parquet").to_csv(
	"data/processed/market_prices_with_rainfall.csv", index=False
)
```

## Data

The raw dataset is stored in `data/raw/dirty_cafe_sales.csv` and has been left unmodified as received.

## Tests

The individual stages can also be run directly and print a summary:

	python -m src.ingest.source_a
	python -m src.ingest.source_b
	python -m src.validate.rules

Run the fast unit tests with:

	python -m pytest -q

## Notes

- `docs/data_source.md`: describes the dataset type, variables, and target/feature candidates.
- `docs/issues_observed.md`: records suspicious values observed during the initial inspection.
- `notebooks/01_inspection.ipynb`: loads the raw file and runs only inspection operations.
