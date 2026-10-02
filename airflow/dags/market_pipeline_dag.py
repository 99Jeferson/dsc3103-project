import airflow.sdk import DAGS, task 
from datetime import datetime, timedelta

from src.ingest.source_a import ingest_source_a

with DAGS (
    dag_id = "market_pipeline",
    schedule = "@daily",
    start_date = datetime (2026,10,2),
    catchup=False
)