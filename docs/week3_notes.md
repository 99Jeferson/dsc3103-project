# Week 3 Notes

For this project, I chose ETL rather than ELT. The sales dataset is the primary operational source, and daily rainfall is fetched from the Open-Meteo Historical Weather API for each project market and joined on market and date. The API response is cached in `data/raw/rainfall.csv`, while the prices are validated and cleaned before loading the final joined Parquet dataset. This keeps bad sales records out of the curated store and makes the API-backed pipeline reproducible offline.

I used overwrite semantics for the processed output. Each run of the pipeline rebuilds the cleaned and merged parquet files from the source inputs, which guarantees the output is current and prevents duplicate rows from being introduced by repeated execution. This is a simple and reliable choice for a lab project with a small, deterministic dataset.
