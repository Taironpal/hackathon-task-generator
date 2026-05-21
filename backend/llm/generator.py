"""Главный pipeline генерации: запрос → JSON → валидация → регенерация."""
import json
import re
import time
from dataclasses import dataclass, field

from pydantic import ValidationError

from backend.llm.gigachat_client import _model_name, chat
from backend.llm.logger import log_call
from backend.llm.prompts import (
    AUDIENCE_INSTRUCTIONS,
    SYSTEM_GENERATOR,
    USER_GENERATE_TEMPLATE,
    USER_REGENERATE_TASK_TEMPLATE,
)
from backend.models import GenerationRequest, Task, Variant, WorkSheet
from backend.validators.math_validator import validate_task_math

MAX_PARSE_ATTEMPTS = 3
MAX_TASK_REGEN = 2
_FENCE_RE = re.compile(r"```(?:json)?\s*|\s*```", re.IGNORECASE)


def _extract_json(text: str) -> str:
    cleaned = _FENCE_RE.sub("", text).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        return cleaned
    return cleaned[start : end + 1]


def _build_user_prompt(req: GenerationRequest) -> str:
    return USER_GENERATE_TEMPLATE.format(
        subject=req.subject,
        grade=req.grade,
        topic=req.topic,
        variants_count=req.variants_count,
        tasks_per_variant=req.tasks_per_variant,
        difficulty=req.difficulty,
        audience_instruction=AUDIENCE_INSTRUCTIONS.get(
            req.audience, AUDIENCE_INSTRUCTIONS["standard"]
        ),
        notes=req.notes or "-",
    )


class GenerationError(RuntimeError):
    pass


@dataclass
class GenerationStats:
    """Метрика качества - для логов и презентации."""

    total_tasks: int = 0
    first_pass_ok: int = 0
    regenerated: int = 0
    failed_after_regen: int = 0
    duplicates_replaced: int = 0
    elapsed_seconds: float = 0.0
    issues: list[str] = field(default_factory=list)

    @property
    def first_pass_rate(self) -> float:
        return self.first_pass_ok / self.total_tasks if self.total_tasks else 0.0


# ---------- генерация всего worksheet ----------


def _generate_raw_worksheet(req: GenerationRequest) -> list[Variant]:
    user_prompt = _build_user_prompt(req)
    model = _model_name()
    last_error: str | None = None

    for attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
        raw = chat(user_prompt, system=SYSTEM_GENERATOR, temperature=0.4)
        payload = _extract_json(raw)
        error: str | None = None
        variants: list[Variant] = []
        try:
            data = json.loads(payload)
            variants = [Variant.model_validate(v) for v in data["variants"]]
            if len(variants) != req.variants_count:
                error = f"expected {req.variants_count} variants, got {len(variants)}"
            else:
                for v in variants:
                    if len(v.tasks) != req.tasks_per_variant:
                        error = (
                            f"variant {v.number}: expected {req.tasks_per_variant} "
                            f"tasks, got {len(v.tasks)}"
                        )
                        break
        except (json.JSONDecodeError, KeyError, ValidationError) as e:
            error = f"{type(e).__name__}: {e}"

        log_call(
            purpose="generate_worksheet",
            model=model,
            system=SYSTEM_GENERATOR,
            user=user_prompt,
            response=raw,
            attempt=attempt,
            error=error,
        )

        if error is None:
            return variants
        last_error = error

    raise GenerationError(
        f"failed to generate worksheet after {MAX_PARSE_ATTEMPTS} attempts. "
        f"Last error: {last_error}"
    )


# ---------- регенерация одной задачи ----------


def _regenerate_single_task(
    req: GenerationRequest,
    existing_statements: list[str],
    reason: str,
) -> Task | None:
    """Перегенерировать одну задачу. Возвращает None при провале."""
    prompt = USER_REGENERATE_TASK_TEMPLATE.format(
        topic=req.topic,
        grade=req.grade,
        difficulty=req.difficulty,
        reason=reason,
        existing_statements="\n".join(f"- {s}" for s in existing_statements) or "-",
    )
    model = _model_name()

    for attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
        raw = chat(prompt, system=SYSTEM_GENERATOR, temperature=0.6)
        payload = _extract_json(raw)
        error: str | None = None
        try:
            data = json.loads(payload)
            task = Task.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            error = f"{type(e).__name__}: {e}"
            task = None  # type: ignore[assignment]

        log_call(
            purpose="regenerate_task",
            model=model,
            system=SYSTEM_GENERATOR,
            user=prompt,
            response=raw,
            attempt=attempt,
            error=error,
        )

        if error is None:
            return task

    return None


# ---------- основная функция ----------


def _statement_key(s: str) -> str:
    """Грубая нормализация для сравнения условий: убираем пробелы и регистр."""
    return re.sub(r"\s+", "", s).lower()


def generate_worksheet(
    req: GenerationRequest,
) -> tuple[WorkSheet, GenerationStats]:
    """Сгенерировать контрольную с валидацией и регенерацией проблемных задач."""
    t0 = time.perf_counter()
    variants = _generate_raw_worksheet(req)
    stats = GenerationStats()

    seen_statements: set[str] = set()

    for variant in variants:
        for idx, task in enumerate(variant.tasks):
            stats.total_tasks += 1

            issues = validate_task_math(task)
            is_dup = _statement_key(task.statement) in seen_statements
            if is_dup:
                issues.append("дубликат условия с другой задачей")

            if not issues:
                stats.first_pass_ok += 1
                seen_statements.add(_statement_key(task.statement))
                continue

            # перегенерируем
            stats.issues.append(
                f"variant {variant.number}, task {idx + 1}: {'; '.join(issues)}"
            )
            replaced = False
            for _ in range(MAX_TASK_REGEN):
                existing = [
                    t.statement
                    for j, t in enumerate(variant.tasks)
                    if j != idx
                ]
                new_task = _regenerate_single_task(
                    req,
                    existing_statements=existing,
                    reason="; ".join(issues),
                )
                if new_task is None:
                    continue
                new_issues = validate_task_math(new_task)
                if _statement_key(new_task.statement) in seen_statements:
                    new_issues.append("дубликат")
                if not new_issues:
                    variant.tasks[idx] = new_task
                    seen_statements.add(_statement_key(new_task.statement))
                    stats.regenerated += 1
                    if is_dup:
                        stats.duplicates_replaced += 1
                    replaced = True
                    break
                issues = new_issues

            if not replaced:
                stats.failed_after_regen += 1
                # оставляем оригинальную задачу - пусть учитель проверит вручную
                seen_statements.add(_statement_key(task.statement))

    stats.elapsed_seconds = time.perf_counter() - t0
    ws = WorkSheet(
        subject=req.subject,
        grade=req.grade,
        topic=req.topic,
        variants=variants,
    )
    return ws, stats


def regenerate_task(
    ws: WorkSheet,
    variant_number: int,
    task_index: int,
    reason: str = "ручной запрос пользователя",
    difficulty: int | None = None,
) -> Task:
    """Перегенерировать конкретную задачу в worksheet. Изменяет ws на месте и возвращает новую задачу."""
    variant = next((v for v in ws.variants if v.number == variant_number), None)
    if variant is None:
        raise ValueError(f"variant {variant_number} not found")
    if not (0 <= task_index < len(variant.tasks)):
        raise ValueError(f"task_index {task_index} out of range")

    old_task = variant.tasks[task_index]
    req = GenerationRequest(
        subject=ws.subject,
        grade=ws.grade,
        topic=ws.topic,
        variants_count=len(ws.variants),
        tasks_per_variant=len(variant.tasks),
        difficulty=difficulty if difficulty is not None else old_task.difficulty,
    )
    existing = [t.statement for j, t in enumerate(variant.tasks) if j != task_index]

    for _ in range(MAX_TASK_REGEN + 1):
        new_task = _regenerate_single_task(req, existing_statements=existing, reason=reason)
        if new_task is None:
            continue
        if not validate_task_math(new_task):
            variant.tasks[task_index] = new_task
            return new_task
    raise GenerationError(
        f"не удалось получить валидную задачу для варианта {variant_number}, "
        f"позиция {task_index + 1}"
    )
