# DSC3103 Project

This repository contains the raw cafe sales dataset used in Lab 1 and the supporting documentation for initial inspection and issue tracking.

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
├── tests/
├── notebooks/
└── docs/
```

## Data

The raw dataset is stored in `data/raw/dirty_cafe_sales.csv` and has been left unmodified as received.

## Notes

- `docs/data_source.md`: describes the dataset type, variables, and target/feature candidates.
- `docs/issues_observed.md`: records suspicious values observed during the initial inspection.
- `notebooks/01_inspection.ipynb`: loads the raw file and runs only inspection operations.
