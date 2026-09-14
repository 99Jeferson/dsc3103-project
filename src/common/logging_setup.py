from __future__ import annotations

import json
import logging
from pathlib import Path

from src.common.config import PIPELINE_LOG_PATH, PIPELINE_TEXT_LOG_PATH


def build_logger(name: str = "dsc3103_pipeline") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_path = Path(PIPELINE_TEXT_LOG_PATH)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(file_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def append_stage_log(entries: list[dict], stage: str, input_rows: int, output_rows: int, errors: list[str] | None = None) -> None:
    entries.append({
        "stage": stage,
        "input_rows": int(input_rows),
        "output_rows": int(output_rows),
        "errors": errors or [],
    })


def write_json_log(entries: list[dict], path: Path = PIPELINE_LOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
