"""End-to-end: эталон → разметка слотов → N вариантов с sympy-сверкой.

    python -m scripts.variants "В магазине было 120 кг яблок..." --grade 5 --count 4
    python -m scripts.variants                               # smoke на 3 эталонах
"""
import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from backend.llm.analyzer import AnalyzeError, analyze_reference
from backend.variant_generator import VariantGenerationError, generate_variants

GOLDEN = [
    ("математика", 5,
     "В магазине было 120 кг яблок. За день продали 25% яблок. Сколько килограммов яблок осталось?"),
    ("математика", 5,
     "Найдите значение выражения: (48,6 + 29,04) · 2."),
    ("математика", 6,
     "Велосипедист проехал 24 км за 2 часа. С какой средней скоростью он ехал?"),
]


def _run_one(statement: str, subject: str, grade: int | None, count: int, seed: int | None) -> int:
    print(f"\n>>> {subject}, класс {grade}, count={count}")
    print(f"    эталон: {statement}")
    try:
        ref = analyze_reference(statement, subject=subject, grade=grade)
    except AnalyzeError as e:
        print(f"[FAIL анализ] {e}")
        return 1

    print(f"[анализ] template = {ref.template}")
    print(f"[анализ] formula  = {ref.answer_formula}")
    print(f"[анализ] slots    = {[(s.name, s.type.value, s.range) for s in ref.slots]}")
    print(f"[анализ] исходный ответ: {ref.original_answer}")

    try:
        variants = generate_variants(ref, count=count, seed=seed)
    except VariantGenerationError as e:
        print(f"[FAIL генерация] {e}")
        return 1

    print(f"\n[сгенерировано {len(variants)} вариантов]")
    for v in variants:
        print(f"\n  Вариант {v.number} (сложность {v.difficulty}/5, sympy ✓):")
        print(f"    {v.statement}")
        print(f"    Ответ: {v.answer}   значения: {v.slot_values}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Эталон → варианты")
    p.add_argument("statement", nargs="?")
    p.add_argument("--subject", default="математика")
    p.add_argument("--grade", type=int, default=None)
    p.add_argument("--count", type=int, default=4)
    p.add_argument("--seed", type=int, default=None)
    args = p.parse_args()

    if args.statement:
        return _run_one(args.statement, args.subject, args.grade, args.count, args.seed)

    print("=== Smoke: 3 эталона → варианты ===")
    failures = 0
    for subject, grade, statement in GOLDEN:
        rc = _run_one(statement, subject, grade, args.count, args.seed)
        if rc != 0:
            failures += 1
    print(f"\nИтого: {len(GOLDEN) - failures}/{len(GOLDEN)} эталонов прошли end-to-end")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
