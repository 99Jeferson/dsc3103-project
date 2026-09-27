# DSC3103 Project

This repository contains the DSC3103 market-price ETL pipeline and Lab 4 analytics
work. Lab 3 cleans market prices and joins them to rainfall; Lab 4 builds and
queries a DuckDB star schema from the assignment-provided joined Parquet file.

## Project structure

```text
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
│   ├── analytics/    # Lab 4 star schema and analytical queries
│   ├── common/       # Paths, environment settings, and logging helpers
│   └── run_pipeline.py  # Single pipeline entry point
├── tests/
└── docs/
```

## Run the pipeline

From the repository root, run the single documented entry point:

```bash
python -m src.run_pipeline
```

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

## Run the Lab 4 analytics assignment

Place the assignment-provided `prices_with_rainfall.parquet` at
`data/processed/prices_with_rainfall.parquet`, then run:

```bash
python -m src.analytics.build_analytics
```

This builds `data/processed/analytics.duckdb`, runs the baseline and five
dimension-joined queries, and compares flat-Parquet and star-schema query times.
The schema diagram and written discussion are in `docs/star_schema_diagram.png`
and `docs/Lab_04_notes.md`. The Lab 3 pipeline writes a separately named output,
`market_prices_with_rainfall.parquet`; it does not create or replace the
assignment-provided Lab 4 input.

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

```bash
python -c "import pandas as pd; print(pd.read_parquet('data/processed/market_prices_with_rainfall.parquet').head())"
```

The Lab 3 pipeline generates:

- `prices_clean.parquet`: cleaned prices before the rainfall join.
- `market_prices_with_rainfall.parquet`: the pipeline's final joined output.

If a spreadsheet or text editor is required, convert a copy rather than
changing the pipeline output:

```python
pd.read_parquet("data/processed/market_prices_with_rainfall.parquet").to_csv(
    "data/processed/market_prices_with_rainfall.csv", index=False
)
```

## Data

The active raw inputs are `data/raw/prices.csv` and the cached rainfall file
`data/raw/rainfall.csv`. The Lab 4 joined input is supplied separately by the
assignment and belongs in `data/processed/prices_with_rainfall.parquet`.

## Tests

The individual stages can also be run directly and print a summary:

```bash
python -m src.ingest.source_a
python -m src.ingest.source_b
python -m src.validate.rules
```

Run the fast unit tests with:

```bash
python -m pytest -q
```

## Notes

- `docs/data_source.md`: describes the active market-price, rainfall, and Lab 4 inputs.
- `docs/issues_observed.md`: summarizes known data-quality issues in the market-price workflow.
- `docs/validation_report.md`: records the raw market-price validation results.
- `docs/cleaning_log.csv`: records cleaning actions from the ETL pipeline.
- `docs/Lab_04_notes.md`: records the Lab 4 schema, query results, and architecture decision.
