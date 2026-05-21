"""Smoke-тест GigaChat API. Запуск: python -m scripts.test_gigachat"""
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv()

from backend.llm.gigachat_client import chat


def main() -> int:
    print(">>> GigaChat ping...")
    try:
        reply = chat(
            "Сгенерируй одно арифметическое задание для 5 класса по теме "
            "«сложение десятичных дробей». Верни одной строкой: условие - ответ.",
            system="Ты - методист по математике. Отвечай кратко.",
        )
    except Exception as e:
        print(f"[FAIL] {type(e).__name__}: {e}")
        return 1
    print("[OK] ответ модели:")
    print(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
