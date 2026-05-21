"""Библиотека эталонных задач. Грузится из data/library.json при старте."""
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

LIBRARY_PATH = Path(__file__).resolve().parents[1] / "data" / "library.json"


class LibraryItem(BaseModel):
    id: str
    grade: int = Field(ge=1, le=11)
    subject: str = "математика"
    topic: str
    subtopic: str = ""
    tags: list[str] = Field(default_factory=list)
    is_combined: bool = False
    statement: str
    textbook: str | None = None  # ссылка на учебник: «Виленкин 5», «Атанасян 7-9», «Перышкин 7»


class Library(BaseModel):
    version: str
    description: str
    items: list[LibraryItem]


def load_library() -> Library:
    with LIBRARY_PATH.open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return Library.model_validate(data)


# Типичные окончания русского, которые отбрасываем при stem-поиске:
# чтобы «обыкновенные» матчилось с «обыкновенных», «дроби» c «дробей» и т.п.
_RU_ENDINGS = (
    "ями", "ыми", "ого", "ому", "ого", "ыми",
    "ие", "ые", "ой", "ей", "ых", "ом", "ам", "ах", "ям", "ях", "ев", "ов",
    "и", "ы", "а", "я", "у", "ю", "е", "о",
)


def _stem(word: str) -> str:
    """Грубый стемминг: отбрасываем часто встречающееся окончание."""
    for end in _RU_ENDINGS:
        if word.endswith(end) and len(word) - len(end) >= 4:
            return word[: -len(end)]
    return word


def _tokens(text: str) -> list[str]:
    """Слова длиной ≥3 в нижнем регистре."""
    return [w for w in (
        "".join(c if c.isalnum() else " " for c in text.lower()).split()
    ) if len(w) >= 3]


def _matches(query: str, haystack: str) -> bool:
    """Все стеммы из query должны встретиться как подстрока в haystack (по стеммам)."""
    q_stems = [_stem(w) for w in _tokens(query)]
    if not q_stems:
        return True
    h_stems = " ".join(_stem(w) for w in _tokens(haystack))
    return all(s in h_stems for s in q_stems)


def search_library(
    lib: Library,
    query: str | None = None,
    grade: int | None = None,
    subject: str | None = None,
    combined_only: bool = False,
) -> list[LibraryItem]:
    items = lib.items
    if subject is not None:
        s = subject.lower().strip()
        items = [i for i in items if i.subject.lower() == s]
    if grade is not None:
        items = [i for i in items if i.grade == grade]
    if combined_only:
        items = [i for i in items if i.is_combined]
    if query:
        items = [
            i for i in items
            if _matches(
                query,
                " ".join([i.topic, i.subtopic, i.statement, *i.tags]),
            )
        ]
    return items
