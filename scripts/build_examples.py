"""Генерирует «золотые» примеры контрольных и сохраняет их в examples/.

Запускается один раз перед демо. Если на защите упадёт GigaChat - показываем эти файлы.
"""
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.exporters.docx_exporter import export_for_students, export_for_teacher
from backend.llm.generator import GenerationError, generate_worksheet
from backend.models import GenerationRequest
from backend.storage import save_worksheet

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"

GOLDEN = [
    {
        "slug": "decimals_standard",
        "title": "Сложение и вычитание десятичных дробей - стандартный класс",
        "req": GenerationRequest(
            grade=5,
            topic="Сложение и вычитание десятичных дробей",
            variants_count=4,
            tasks_per_variant=5,
            difficulty=3,
            audience="standard",
        ),
    },
    {
        "slug": "decimals_weak",
        "title": "Сложение и вычитание десятичных дробей - для отстающих",
        "req": GenerationRequest(
            grade=5,
            topic="Сложение и вычитание десятичных дробей",
            variants_count=2,
            tasks_per_variant=4,
            difficulty=2,
            audience="weak",
        ),
    },
    {
        "slug": "multiply_decimals_strong",
        "title": "Умножение десятичных дробей - для сильных учеников",
        "req": GenerationRequest(
            grade=5,
            topic="Умножение десятичных дробей",
            variants_count=4,
            tasks_per_variant=5,
            difficulty=4,
            audience="strong",
        ),
    },
]


def main() -> int:
    EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    report_lines: list[str] = ["# Золотые примеры", ""]

    for spec in GOLDEN:
        slug = spec["slug"]
        title = spec["title"]
        req: GenerationRequest = spec["req"]
        print(f"\n>>> {title}")
        t0 = time.perf_counter()
        try:
            ws, stats = generate_worksheet(req)
        except GenerationError as e:
            print(f"   [FAIL] {e}")
            continue
        elapsed = time.perf_counter() - t0

        save_worksheet(ws, f"examples_{slug}")
        json_dst = EXAMPLES_DIR / f"{slug}.json"
        json_dst.write_text(
            ws.model_dump_json(indent=2), encoding="utf-8"
        )
        students_path = export_for_students(ws, EXAMPLES_DIR / f"{slug}_варианты.docx")
        teacher_path = export_for_teacher(ws, EXAMPLES_DIR / f"{slug}_ключи.docx")
        print(
            f"   [OK] {req.variants_count}×{req.tasks_per_variant} задач, "
            f"first-pass {stats.first_pass_rate:.0%}, "
            f"{elapsed:.1f}s, regen={stats.regenerated}"
        )
        report_lines += [
            f"## {title}",
            f"- параметры: {req.variants_count} вариантов × {req.tasks_per_variant} задач, "
            f"сложность {req.difficulty}, аудитория `{req.audience}`",
            f"- качество: {stats.first_pass_rate:.0%} с первого раза, "
            f"перегенерировано {stats.regenerated}, время {elapsed:.1f} с",
            f"- файлы: [{slug}.json]({slug}.json), "
            f"[варианты]({students_path.name}), [ключи]({teacher_path.name})",
            "",
        ]

    (EXAMPLES_DIR / "README.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\nГотово. Файлы в {EXAMPLES_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
