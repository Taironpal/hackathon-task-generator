"""Генерация вариантов из ReferenceTask: подбор значений слотов + sympy-сверка.

Полностью локальная логика, БЕЗ обращения к LLM. LLM только размечает эталон;
дальше арифметика и валидация делаются sympy + Python.
"""
import random
from decimal import Decimal
from fractions import Fraction
from typing import Any

from sympy import Rational

from backend.llm.analyzer import evaluate_formula
from backend.models import GeneratedVariant, ReferenceTask, Slot, SlotType
from backend.russian_morph import fix_agreement

MAX_PICK_ATTEMPTS = 50
MAX_VARIANT_ATTEMPTS = 80


class VariantGenerationError(RuntimeError):
    pass


def _pick_int(rng: tuple[float, float], rnd: random.Random) -> int:
    lo, hi = int(rng[0]), int(rng[1])
    return rnd.randint(lo, hi)


def _pick_decimal(rng: tuple[float, float], rnd: random.Random) -> float:
    """Десятичное с 1-2 знаками после запятой."""
    lo, hi = rng
    raw = rnd.uniform(lo, hi)
    return round(raw, 2)


def _pick_percent(rng: tuple[float, float], rnd: random.Random) -> int:
    """Процент целым числом - обычно школьные задачи без сотых процента."""
    lo, hi = max(0, int(rng[0])), min(100, int(rng[1]))
    return rnd.randint(lo, hi)


def _pick_fraction(rng: tuple[float, float], rnd: random.Random) -> str:
    """Простая дробь со знаменателем 2-12."""
    lo = int(rng[0]) if rng else 1
    hi = int(rng[1]) if rng else 12
    denom = rnd.randint(max(2, lo), max(3, hi))
    numer = rnd.randint(1, denom - 1)
    return f"{numer}/{denom}"


def _pick_slot_value(slot: Slot, rnd: random.Random) -> Any:
    if slot.locked:
        return slot.original
    if slot.type == SlotType.STRING:
        if slot.options:
            return rnd.choice(slot.options)
        return slot.original
    rng = slot.range or (1.0, 10.0)
    if slot.type == SlotType.INT:
        return _pick_int(rng, rnd)
    if slot.type == SlotType.DECIMAL:
        return _pick_decimal(rng, rnd)
    if slot.type == SlotType.PERCENT:
        return _pick_percent(rng, rnd)
    if slot.type == SlotType.FRACTION:
        return _pick_fraction(rng, rnd)
    return slot.original


def _is_finite_decimal(value: Rational) -> bool:
    """Проверяет, что рациональное представимо конечной десятичной дробью.
    Знаменатель в несократимом виде содержит только множители 2 и 5."""
    denom = int(value.q)
    while denom % 2 == 0:
        denom //= 2
    while denom % 5 == 0:
        denom //= 5
    return denom == 1


def _format_answer(value: Rational) -> str:
    """Форматирует ответ для ученика: целое или десятичная дробь."""
    if value.q == 1:
        return str(value.p)
    if _is_finite_decimal(value):
        # Decimal без потерь
        d = Decimal(value.p) / Decimal(value.q)
        s = format(d.normalize(), "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s
    # На крайний случай - обыкновенная дробь
    return f"{value.p}/{value.q}"


def _format_slot_for_statement(value: Any, slot_type: SlotType) -> str:
    """Как подставлять значение в условие, чтобы выглядело по-русски."""
    if isinstance(value, float):
        s = f"{value:.2f}".rstrip("0").rstrip(".")
        return s.replace(".", ",")
    if isinstance(value, str) and "/" in value:
        return value
    return str(value)


def _render_statement(template: str, values: dict[str, Any], slot_types: dict[str, SlotType]) -> str:
    formatted = {
        name: _format_slot_for_statement(v, slot_types.get(name, SlotType.STRING))
        for name, v in values.items()
    }
    return fix_agreement(template.format(**formatted))


def _score_difficulty(values: dict[str, Any], baseline: int) -> int:
    """Эвристика сложности по подобранным значениям. 1-5."""
    score = float(baseline)
    for v in values.values():
        if isinstance(v, int):
            digits = len(str(abs(v)))
            score += (digits - 2) * 0.3
            if v % 10 == 0:
                score -= 0.4  # круглые проще
        elif isinstance(v, float):
            score += 0.5
            # сотые сложнее десятых
            if round(v * 100) % 10 != 0:
                score += 0.3
        elif isinstance(v, str) and "/" in v:
            score += 0.6
    return max(1, min(5, int(round(score))))


def _generate_one_variant(
    ref: ReferenceTask,
    number: int,
    seen: set[tuple],
    rnd: random.Random,
) -> GeneratedVariant | None:
    slot_types = {s.name: s.type for s in ref.slots}

    for _ in range(MAX_PICK_ATTEMPTS):
        values: dict[str, Any] = {s.name: _pick_slot_value(s, rnd) for s in ref.slots}
        key = tuple(values[s.name] for s in ref.slots)
        if key in seen:
            continue

        try:
            answer = evaluate_formula(ref.answer_formula, values)
        except (ValueError, TypeError, ArithmeticError) as e:
            continue

        # Бракуем некрасивые ответы (бесконечная дробь)
        if not _is_finite_decimal(answer):
            continue
        # Бракуем отрицательные ответы для большинства школьных задач.
        # Тема явно про отрицательные числа / координаты / температуру разрешает их.
        allow_negative = any(
            kw in (ref.topic + " " + ref.raw_statement).lower()
            for kw in ("отрицательн", "координат", "температур", "разность температур")
        )
        if answer < 0 and not allow_negative:
            continue
        # Нули в задачах с естественными количествами (купил, осталось, потратил) методически странные
        suggests_positive = any(
            kw in ref.raw_statement.lower()
            for kw in ("сдач", "осталось", "осталс", "потратил", "купил", "продал")
        )
        if answer == 0 and suggests_positive:
            continue

        seen.add(key)
        statement = _render_statement(ref.template, values, slot_types)
        difficulty = _score_difficulty(values, ref.difficulty_baseline)

        return GeneratedVariant(
            number=number,
            statement=statement,
            slot_values=values,
            answer=_format_answer(answer),
            solution=None,
            difficulty=difficulty,
            sympy_verified=True,
            issues=[],
        )

    return None


def generate_variants(
    ref: ReferenceTask,
    count: int = 4,
    seed: int | None = None,
) -> list[GeneratedVariant]:
    """Генерирует count уникальных вариантов. Каждый математически сверен sympy.

    Если за MAX_VARIANT_ATTEMPTS не удалось собрать count, возвращает то, что есть.
    """
    rnd = random.Random(seed)
    variants: list[GeneratedVariant] = []
    seen: set[tuple] = set()

    for n in range(1, count + 1):
        variant = None
        for _ in range(MAX_VARIANT_ATTEMPTS):
            variant = _generate_one_variant(ref, n, seen, rnd)
            if variant is not None:
                break
        if variant is None:
            raise VariantGenerationError(
                f"не удалось собрать вариант {n} за {MAX_VARIANT_ATTEMPTS} попыток - "
                f"возможно, диапазоны слотов слишком узкие или формула даёт некрасивые ответы"
            )
        variants.append(variant)

    return variants
