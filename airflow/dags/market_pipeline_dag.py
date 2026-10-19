"""Airflow DAG for the DSC3103 market-price ETL and analytics pipeline."""

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
from src.common.config import SOURCE_A_RAW_PATH
from src.ingest.source_a import ingest_source_a

from airflow.sdk import dag, get_current_context, task

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[2]))
CLEAN_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "prices_clean_dag.parquet"
JOINED_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "prices_with_rainfall.parquet"
REPORT_PATH = PROJECT_ROOT / "docs" / "airflow_run_report.json"


def _make_project_importable() -> None:
    """Make the mounted project package available inside Airflow task processes."""
    project_root = str(PROJECT_ROOT)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


@dag(
    dag_id="market_pipeline",
    description="Ingest prices and rainfall, clean and join them, build analytics, and report row counts.",
    start_date=datetime(2026, 8, 1),
    schedule="@daily",
    catchup=False,
    tags=["market", "etl", "lab-05"],
)
def market_pipeline():
    @task(task_id="acquire_a", retries=0)
    def acquire_a() -> dict[str, str | int]:
        """Read and validate the local prices CSV; deterministic file errors do not retry."""
        _make_project_importable()
        prices = ingest_source_a(SOURCE_A_RAW_PATH)
        return {"path": str(SOURCE_A_RAW_PATH), "rows": len(prices)}

    @task(
        task_id="acquire_b",
        retries=2,
        retry_delay=timedelta(minutes=1),
    )
    def acquire_b() -> dict[str, str | int]:
        """Load cached rainfall or fetch it; retry to tolerate transient API failures."""
        _make_project_importable()
        from src.common.config import SOURCE_B_RAW_PATH
        from src.ingest.source_b import ingest_source_b

        rainfall = ingest_source_b()
        return {"path": str(SOURCE_B_RAW_PATH), "rows": len(rainfall)}

    @task(task_id="clean_prices", retries=0)
    def clean(
        source_a_result: dict[str, str | int],
        source_b_result: dict[str, str | int],
    ) -> dict[str, str | int]:
        """Clean prices after both source tasks finish; data/schema errors are deterministic."""
        _make_project_importable()
        from src.common.config import CLEANING_LOG_PATH
        from src.ingest.source_a import ingest_source_a
        from src.transform.clean import clean_data

        if not Path(str(source_b_result["path"])).is_file():
            raise FileNotFoundError(f"Source B file not found: {source_b_result['path']}")

        prices = ingest_source_a(str(source_a_result["path"]))
        cleaned, cleaning_log = clean_data(
            df=prices,
            output_path=CLEAN_OUTPUT_PATH,
            log_path=CLEANING_LOG_PATH,
        )
        return {
            "path": str(CLEAN_OUTPUT_PATH),
            "rows": len(cleaned),
            "rules_triggered": len(cleaning_log),
        }

    @task(task_id="join_prices_and_rainfall", retries=0)
    def merge(
        clean_result: dict[str, str | int],
        source_b_result: dict[str, str | int],
    ) -> dict[str, str | int]:
        """Join the cleaned price parquet with normalized rainfall observations."""
        _make_project_importable()
        import pandas as pd

        from src.ingest.source_b import ingest_source_b
        from src.transform.merge import merge_prices_with_rainfall

        cleaned_prices = pd.read_parquet(str(clean_result["path"]))
        rainfall = ingest_source_b(str(source_b_result["path"]))
        joined = merge_prices_with_rainfall(cleaned_prices, rainfall)
        JOINED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        joined.to_parquet(JOINED_OUTPUT_PATH, index=False)
        return {"path": str(JOINED_OUTPUT_PATH), "rows": len(joined)}

    @task(
        task_id="store_star_schema",
        retries=1,
        retry_delay=timedelta(seconds=30),
    )
    def store(merge_result: dict[str, str | int]) -> dict[str, str | int]:
        """Build the idempotent DuckDB star schema; retry once for a transient DB lock."""
        _make_project_importable()
        from src.analytics.build_analytics import DB_PATH, RAW_JOINED_PATH, build_star_schema

        if Path(str(merge_result["path"])) != RAW_JOINED_PATH:
            raise ValueError(
                f"Analytics expects {RAW_JOINED_PATH}, got {merge_result['path']}"
            )
        build_star_schema()
        return {"db_path": str(DB_PATH), "input_rows": int(merge_result["rows"])}

    @task(task_id="report_fact_table", retries=0)
    def report(store_result: dict[str, str | int]) -> dict[str, str | int]:
        """Return and persist a structured run report containing the fact row count."""
        import duckdb

        with duckdb.connect(str(store_result["db_path"]), read_only=True) as connection:
            row_count = connection.execute(
                "SELECT COUNT(*) FROM fact_price_observation"
            ).fetchone()[0]

        context = get_current_context()
        logical_date = context.get("logical_date")
        run_date = (
            logical_date.date().isoformat()
            if logical_date is not None
            else datetime.now(timezone.utc).date().isoformat()
        )
        report_data: dict[str, str | int] = {
            "run_date": run_date,
            "run_id": str(context["run_id"]),
            "fact_table_row_count": int(row_count),
            "joined_input_row_count": int(store_result["input_rows"]),
            "database": str(store_result["db_path"]),
        }
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(json.dumps(report_data, indent=2) + "\n", encoding="utf-8")
        return report_data

    prices = acquire_a()
    rainfall = acquire_b()
    cleaned = clean(prices, rainfall)
    joined = merge(cleaned, rainfall)
    stored = store(joined)
    report(stored)


market_pipeline_dag = market_pipeline()
