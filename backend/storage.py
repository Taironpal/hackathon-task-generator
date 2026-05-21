import json
import os
from pathlib import Path

from backend.models import WorkSheet

STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "./data"))


def save_worksheet(worksheet: WorkSheet, name: str) -> Path:
    STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    path = STORAGE_PATH / f"{name}.json"
    path.write_text(worksheet.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_worksheet(name: str) -> WorkSheet:
    path = STORAGE_PATH / f"{name}.json"
    return WorkSheet.model_validate(json.loads(path.read_text(encoding="utf-8")))
