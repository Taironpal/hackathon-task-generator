"""CLI для генерации контрольной без UI/HTTP.

Пример:
    python -m scripts.generate --topic "Действия с десятичными дробями" --grade 5 --variants 4 --tasks 5
"""
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from backend.llm.generator import GenerationError, generate_worksheet
from backend.models import GenerationRequest
from backend.storage import save_worksheet


def main() -> int:
    p = argparse.ArgumentParser(description="Сгенерировать контрольную работу")
    p.add_argument("--subject", default="математика")
    p.add_argument("--grade", type=int, default=5)
    p.add_argument("--topic", required=True, help="Тема контрольной")
    p.add_argument("--variants", type=int, default=4, dest="variants_count")
    p.add_argument("--tasks", type=int, default=5, dest="tasks_per_variant")
    p.add_argument("--difficulty", type=int, default=3, choices=range(1, 6))
    p.add_argument(
        "--audience", default="standard", choices=["standard", "weak", "strong"]
    )
    p.add_argument("--notes", default=None)
    args = p.parse_args()

    req = GenerationRequest(
        subject=args.subject,
        grade=args.grade,
        topic=args.topic,
        variants_count=args.variants_count,
        tasks_per_variant=args.tasks_per_variant,
        difficulty=args.difficulty,
        audience=args.audience,
        notes=args.notes,
    )

    print(
        f">>> {req.subject}, {req.grade} класс, тема «{req.topic}»: "
        f"{req.variants_count} вариантов × {req.tasks_per_variant} задач"
    )
    try:
        ws, stats = generate_worksheet(req)
    except GenerationError as e:
        print(f"[FAIL] {e}")
        return 1

    name = f"{ws.subject}_{ws.grade}_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}"
    path = save_worksheet(ws, name)
    print(f"[OK] сохранено: {path}")
    for v in ws.variants:
        print(f"\n--- Вариант {v.number} ---")
        for i, t in enumerate(v.tasks, 1):
            print(f"{i}. {t.statement}")
            print(f"   Ответ: {t.answer}")

    print("\n=== Качество ===")
    print(f"  время генерации: {stats.elapsed_seconds:.1f} с")
    print(
        f"  всего задач: {stats.total_tasks}, "
        f"с первого раза ок: {stats.first_pass_ok} "
        f"({stats.first_pass_rate:.0%})"
    )
    print(f"  перегенерировано: {stats.regenerated}")
    print(f"  заменено дубликатов: {stats.duplicates_replaced}")
    print(f"  не удалось починить: {stats.failed_after_regen}")
    if stats.issues:
        print("  --- найденные проблемы ---")
        for i in stats.issues:
            print(f"    • {i}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
