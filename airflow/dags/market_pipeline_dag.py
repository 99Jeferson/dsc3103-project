"""Airflow DAG for the DSC3103 market-price ETL pipeline."""

from datetime import datetime
import os
from pathlib import Path
import sys

from airflow.sdk import dag, task

from src.ingest.source_a import ingest_source_a
from src.common.config import SOURCE_A_RAW_PATH

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[2]))


@dag(
    dag_id="market_pipeline",
    description="Clean market prices and join them with rainfall data.",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["market", "etl"],
)
def market_pipeline():
    @task(task_id="run_market_pipeline")
    def run_pipeline() -> None:
        project_root = str(PROJECT_ROOT)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from src.run_pipeline import main

        main()

    run_pipeline()


market_pipeline_dag = market_pipeline()

@task
def acquire_():
    df = ingest_source_a(SOURCE_A_RAW_PATH)

    return {"path": SOURCE_A_RAW_PATH, "rows" : len(df) }

a = acquire_()