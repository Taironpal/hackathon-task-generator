"""JSONL-логгер запросов к LLM. Сохраняем всё - пригодится для отладки и презентации."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

LOG_PATH = Path(os.getenv("LLM_LOG_PATH", "./data/llm_logs"))


def log_call(
    *,
    purpose: str,
    model: str,
    system: str | None,
    user: str,
    response: str,
    attempt: int = 1,
    error: str | None = None,
) -> str:
    LOG_PATH.mkdir(parents=True, exist_ok=True)
    call_id = uuid4().hex[:12]
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "call_id": call_id,
        "purpose": purpose,
        "model": model,
        "attempt": attempt,
        "system": system,
        "user": user,
        "response": response,
        "error": error,
    }
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with (LOG_PATH / f"{day}.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return call_id
