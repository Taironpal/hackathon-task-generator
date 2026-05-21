"""Анализатор эталонной задачи: текст → ReferenceTask со слотами и формулой ответа."""
import json
import re
import string
from typing import Any

from pydantic import ValidationError
from sympy import Rational, nsimplify, sympify
from sympy.core.sympify import SympifyError

from backend.llm.gigachat_client import _model_name, chat
from backend.llm.logger import log_call
from backend.llm.prompts import SYSTEM_ANALYZER, USER_ANALYZE_TEMPLATE
from backend.models import ReferenceTask, Slot, SlotType

MAX_PARSE_ATTEMPTS = 3
_FENCE_RE = re.compile(r"```(?:json)?\s*|\s*```", re.IGNORECASE)
_FORMATTER = string.Formatter()


class AnalyzeError(RuntimeError):
    pass


def _extract_json(text: str) -> str:
    cleaned = _FENCE_RE.sub("", text).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        return cleaned
    return cleaned[start : end + 1]


def _template_slot_names(template: str) -> set[str]:
    names: set[str] = set()
    for _, field_name, _, _ in _FORMATTER.parse(template):
        if field_name:
            names.add(field_name)
    return names


def _to_rational(value: Any) -> Rational | None:
    """Привести значение к точному рациональному. None если не число."""
    if value is None:
        return None
    try:
        if isinstance(value, str):
            v = value.strip().replace(",", ".")
            return nsimplify(sympify(v), rational=True)
        return nsimplify(sympify(value), rational=True)
    except (SympifyError, SyntaxError, TypeError, ValueError):
        return None


def evaluate_formula(formula: str, values: dict[str, Any]) -> Rational:
    """Подставить значения в формулу, вернуть точное рациональное."""
    expr = sympify(formula)
    rational_values = {}
    for name, v in values.items():
        r = _to_rational(v)
        if r is None:
            raise ValueError(f"значение {name}={v!r} не приводится к числу")
        rational_values[name] = r
    return nsimplify(expr.subs(rational_values), rational=True)


def _validate_reference(ref: ReferenceTask) -> list[str]:
    """Семантическая проверка. Возвращает список проблем (пустой = ок)."""
    issues: list[str] = []

    template_slots = _template_slot_names(ref.template)
    declared = {s.name for s in ref.slots}

    missing_in_slots = template_slots - declared
    if missing_in_slots:
        issues.append(f"в шаблоне есть слоты, не описанные в slots: {sorted(missing_in_slots)}")
    missing_in_template = declared - template_slots
    if missing_in_template:
        issues.append(f"в slots описаны имена, отсутствующие в шаблоне: {sorted(missing_in_template)}")

    try:
        expr = sympify(ref.answer_formula)
    except (SympifyError, SyntaxError, TypeError) as e:
        issues.append(f"answer_formula не парсится sympy: {e}")
        return issues

    formula_symbols = {str(s) for s in expr.free_symbols}
    unknown_in_formula = formula_symbols - declared
    if unknown_in_formula:
        issues.append(
            f"answer_formula использует имена, не объявленные в slots: {sorted(unknown_in_formula)}"
        )

    for slot in ref.slots:
        if slot.type in (SlotType.INT, SlotType.DECIMAL, SlotType.PERCENT):
            if slot.range is None:
                issues.append(f"слот {slot.name}: нет range для числового типа")
                continue
            lo, hi = slot.range
            if lo >= hi:
                issues.append(f"слот {slot.name}: некорректный диапазон [{lo}, {hi}]")
            if slot.type == SlotType.PERCENT and not (0 <= lo and hi <= 100):
                issues.append(f"слот {slot.name}: процент вне [0, 100]")

    return issues


def _cross_check_original_answer(ref: ReferenceTask) -> str | None:
    """Возвращает текст предупреждения, если original_answer от LLM не сходится с формулой.
    Это НЕ ошибка анализа: формула важнее, sympy всё равно посчитает правильно для вариантов."""
    if not ref.original_answer:
        return None
    try:
        original_values = {s.name: s.original for s in ref.slots}
        computed = evaluate_formula(ref.answer_formula, original_values)
        stated = _to_rational(ref.original_answer)
        if stated is None or computed == stated:
            return None
        return (
            f"внимание: LLM указала original_answer={ref.original_answer}, "
            f"но формула на исходных значениях даёт {computed}. Используется формула."
        )
    except (ValueError, SympifyError, TypeError) as e:
        return f"внимание: не удалось перекрёстно проверить original_answer ({e})"


def _coerce_slot(raw: dict) -> Slot:
    """Достаём слот из сырого JSON-словаря, переводя range к tuple."""
    raw = dict(raw)
    rng = raw.get("range")
    if isinstance(rng, list) and len(rng) == 2:
        raw["range"] = tuple(rng)
    return Slot(**raw)


def _parse_reference(raw_json: str, raw_statement: str, subject: str, grade: int | None) -> ReferenceTask:
    data: dict[str, Any] = json.loads(_extract_json(raw_json))
    slots = [_coerce_slot(s) for s in data.get("slots", [])]
    return ReferenceTask(
        raw_statement=raw_statement,
        template=data["template"],
        slots=slots,
        answer_formula=data["answer_formula"],
        original_answer=data.get("original_answer"),
        topic=data.get("topic", "-"),
        subject=subject,
        grade=grade,
        difficulty_baseline=int(data.get("difficulty_baseline", 3)),
    )


def analyze_reference(
    raw_statement: str,
    subject: str = "математика",
    grade: int | None = None,
) -> ReferenceTask:
    """Главная точка входа. Бросает AnalyzeError, если за MAX_PARSE_ATTEMPTS не получилось."""
    user_prompt = USER_ANALYZE_TEMPLATE.format(
        raw_statement=raw_statement.strip(),
        subject=subject,
        grade_hint=str(grade) if grade is not None else "не указан",
    )

    last_error: str | None = None
    for attempt in range(1, MAX_PARSE_ATTEMPTS + 1):
        response = ""
        try:
            response = chat(user_prompt, system=SYSTEM_ANALYZER, temperature=0.2)
            ref = _parse_reference(response, raw_statement, subject, grade)
            issues = _validate_reference(ref)
            if issues:
                raise ValueError("; ".join(issues))
            warning = _cross_check_original_answer(ref)
            log_call(
                purpose="analyze_reference",
                model=_model_name(),
                system=SYSTEM_ANALYZER,
                user=user_prompt,
                response=response,
                attempt=attempt,
                error=warning,
            )
            return ref
        except (json.JSONDecodeError, KeyError, ValueError, ValidationError) as e:
            last_error = str(e)
            log_call(
                purpose="analyze_reference",
                model=_model_name(),
                system=SYSTEM_ANALYZER,
                user=user_prompt,
                response=response,
                attempt=attempt,
                error=last_error,
            )
            user_prompt = (
                USER_ANALYZE_TEMPLATE.format(
                    raw_statement=raw_statement.strip(),
                    subject=subject,
                    grade_hint=str(grade) if grade is not None else "не указан",
                )
                + f"\n\nПредыдущая попытка содержала ошибку: {last_error}. Исправь и верни корректный JSON."
            )

    raise AnalyzeError(f"не удалось разобрать эталон за {MAX_PARSE_ATTEMPTS} попыток: {last_error}")
