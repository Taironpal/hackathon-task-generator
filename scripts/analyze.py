"""CLI-смоук для анализатора эталона.

Передай эталонную задачу аргументом или через stdin:
    python -m scripts.analyze "В магазине было 120 кг яблок. Продали 25%. Сколько осталось?"
    python -m scripts.analyze --grade 5 --file ref.txt
    echo "Найдите 30% от 240." | python -m scripts.analyze --stdin

Без аргументов - прогон по 3 встроенным эталонам (smoke test).
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

GOLDEN_REFERENCES = [
    {
        "subject": "математика",
        "grade": 5,
        "statement": (
            "В магазине было 120 кг яблок. За день продали 25% яблок. "
            "Сколько килограммов яблок осталось в магазине?"
        ),
    },
    {
        "subject": "математика",
        "grade": 5,
        "statement": (
            "Найдите значение выражения: (48,6 + 29,04) · 2."
        ),
    },
    {
        "subject": "математика",
        "grade": 6,
        "statement": (
            "Велосипедист проехал 24 км за 2 часа. С какой средней скоростью он ехал?"
        ),
    },
]


def _print_reference(ref) -> None:
    payload = ref.model_dump(mode="json")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _run_one(statement: str, subject: str, grade: int | None) -> int:
    print(f"\n>>> {subject}, класс {grade}, эталон:")
    print(f"    {statement}")
    try:
        ref = analyze_reference(statement, subject=subject, grade=grade)
    except AnalyzeError as e:
        print(f"[FAIL] {e}")
        return 1
    print("[OK] разобрано:")
    _print_reference(ref)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Анализатор эталонной задачи (Case 4)")
    p.add_argument("statement", nargs="?", help="эталонная задача одной строкой")
    p.add_argument("--subject", default="математика")
    p.add_argument("--grade", type=int, default=None)
    p.add_argument("--file", help="путь к файлу с эталонной задачей")
    p.add_argument("--stdin", action="store_true", help="прочитать эталон из stdin")
    args = p.parse_args()

    if args.statement:
        return _run_one(args.statement, args.subject, args.grade)
    if args.file:
        return _run_one(Path(args.file).read_text(encoding="utf-8"), args.subject, args.grade)
    if args.stdin:
        return _run_one(sys.stdin.read(), args.subject, args.grade)

    # smoke test по встроенным эталонам
    print("=== Smoke test: 3 эталона ===")
    failures = 0
    for ref_def in GOLDEN_REFERENCES:
        rc = _run_one(ref_def["statement"], ref_def["subject"], ref_def["grade"])
        if rc != 0:
            failures += 1
    print(f"\nИтого: {len(GOLDEN_REFERENCES) - failures}/{len(GOLDEN_REFERENCES)} успешно")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
