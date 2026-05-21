import json

from backend.llm.gigachat_client import chat
from backend.llm.prompts import SYSTEM_VALIDATOR
from backend.models import Task


def validate_task(task: Task) -> tuple[bool, list[str]]:
    user_msg = (
        f"Условие: {task.statement}\n"
        f"Ответ: {task.answer}\n"
        f"Решение: {task.solution}\n"
        f"Класс/тема: {task.topic}"
    )
    raw = chat(user_msg, system=SYSTEM_VALIDATOR)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return False, ["validator returned non-JSON"]
    return bool(data.get("ok")), list(data.get("issues", []))
