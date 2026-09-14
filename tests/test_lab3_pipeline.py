from pathlib import Path

import pandas as pd
import pytest

from src.ingest import source_b
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


def test_get_mkt_rainfall_parses_open_meteo_response(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def read(self):
            return b'{"daily": {"time": ["2020-01-01"], "precipitation_sum": [4.2]}}'

    requested = {}

    def fake_urlopen(url, timeout):
        requested["url"] = url
        requested["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(source_b, "urlopen", fake_urlopen)
    result = source_b.get_mkt_rainfall("mukono", 0.3533, 32.7556, "2020-01-01", "2020-01-01")

    assert result.to_dict("records") == [
        {"market": "mukono", "date": "2020-01-01", "rainfall_mm": 4.2}
    ]
    assert "precipitation_sum" in requested["url"]
    assert "latitude=0.3533" in requested["url"]


def test_clean_data_rejects_all_missing_markets(tmp_path):
    df = pd.DataFrame(
        {
            "id": [1],
            "date": ["2020-01-01"],
            "market": [None],
            "commodity": ["Beans"],
            "price": [500],
        }
    )

    with pytest.raises(ValueError, match="every market value is missing"):
        clean_data(df=df, output_path=tmp_path / "clean.parquet", log_path=tmp_path / "clean.csv")
