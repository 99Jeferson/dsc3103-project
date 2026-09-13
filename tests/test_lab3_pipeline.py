from pathlib import Path

import pandas as pd
import pytest

from src.ingest.source_b import ingest_source_b
from src.transform.clean import clean_data


def test_clean_data_imputes_missing_market_and_normalizes_commodities():
    df = pd.DataFrame(
        {
            "id": [1, 2],
            "date": ["2020-01-01", "2020-01-02"],
            "market": [None, "Nakasero"],
            "commodity": ["BEANS", "maize"],
            "price": [500, 500],
        }
    )

    cleaned, log = clean_data(df=df, output_path=Path("data/test_clean_output.parquet"), log_path=Path("docs/test_clean_log.csv"))

    assert cleaned["market"].isna().sum() == 0
    assert set(cleaned["commodity"].unique()) <= {"Beans", "Maize"}
    assert any(entry["rule"] == "missing_market" for entry in log)


def test_ingest_source_b_rejects_schema_mismatch(tmp_path):
    bad_csv = tmp_path / "bad_rainfall.csv"
    pd.DataFrame({"market": ["Nakasero"], "rain": [10]}).to_csv(bad_csv, index=False)

    with pytest.raises(ValueError, match="Expected columns"):
        ingest_source_b(str(bad_csv))
