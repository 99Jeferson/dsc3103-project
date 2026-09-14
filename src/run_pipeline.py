"""Run the data quality validation and cleaning pipeline for the project."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from src.common.config import FINAL_PROCESSED_PATH, PIPELINE_LOG_PATH, PROCESSED_PATH, SOURCE_A_RAW_PATH, SOURCE_B_RAW_PATH
from src.common.logging_setup import append_stage_log, build_logger, write_json_log
from src.ingest.source_a import ingest_source_a
from src.ingest.source_b import ingest_source_b
from src.transform.clean import clean_data


def main() -> None:
    logger = build_logger("dsc3103_pipeline")
    stage_log: list[dict] = []

    logger.info("stage=start ingest_source_a")
    source_a = ingest_source_a(SOURCE_A_RAW_PATH)
    append_stage_log(stage_log, "ingest_source_a", len(source_a), len(source_a))
    logger.info("ingest_source_a rows_in=%s rows_out=%s", len(source_a), len(source_a))

    logger.info("stage=start ingest_source_b")
    source_b = ingest_source_b(SOURCE_B_RAW_PATH)
    append_stage_log(stage_log, "ingest_source_b", len(source_b), len(source_b))
    logger.info("ingest_source_b rows_in=%s rows_out=%s", len(source_b), len(source_b))

    logger.info("stage=start clean_data")
    cleaned_df, cleaning_log = clean_data(
        df=source_a,
        output_path=PROCESSED_PATH,
    )
    append_stage_log(stage_log, "clean_data", len(source_a), len(cleaned_df))
    logger.info("clean_data rows_in=%s rows_out=%s", len(source_a), len(cleaned_df))

    logger.info("stage=start join_market_weather")
    cleaned_df["market"] = cleaned_df["market"].astype(str).str.strip().str.casefold()
    source_b["market"] = source_b["market"].astype(str).str.strip().str.casefold()
    merged = cleaned_df.merge(source_b, how="left", on=["market", "date"])
    final_path = FINAL_PROCESSED_PATH
    final_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(final_path, index=False)
    append_stage_log(stage_log, "join_market_weather", len(cleaned_df), len(merged))
    logger.info("join_market_weather rows_in=%s rows_out=%s", len(cleaned_df), len(merged))

    write_json_log(stage_log, PIPELINE_LOG_PATH)
    logger.info("pipeline complete output=%s", final_path)
    print(f"Processed rows from source A: {len(source_a)}")
    print(f"Processed rows after cleaning: {len(cleaned_df)}")
    print(f"Output dataset written to {final_path}")
    print(f"Cleaning actions recorded: {len(cleaning_log)}")


if __name__ == "__main__":
    main()
