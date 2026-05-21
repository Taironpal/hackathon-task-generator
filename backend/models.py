from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class Task(BaseModel):
    statement: str
    answer: str
    expression: str | None = None  # каноничное арифметическое выражение для sympy
    solution: str
    grading_criteria: str
    difficulty: int = Field(ge=1, le=5)
    topic: str


class Variant(BaseModel):
    number: int
    tasks: list[Task]


class WorkSheet(BaseModel):
    subject: str
    grade: int
    topic: str
    variants: list[Variant]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GenerationRequest(BaseModel):
    subject: str = "математика"
    grade: int
    topic: str
    variants_count: int = 4
    tasks_per_variant: int = 5
    difficulty: int = 3
    audience: str = "standard"  # standard | weak | strong - для дифференцированной подачи
    notes: str | None = None


# ---------- Case 4: анализ эталонной задачи со слотами ----------


class SlotType(str, Enum):
    INT = "int"
    DECIMAL = "decimal"
    PERCENT = "percent"
    FRACTION = "fraction"
    STRING = "string"


class Slot(BaseModel):
    name: str
    original: Any
    type: SlotType
    range: tuple[float, float] | None = None
    options: list[Any] | None = None
    locked: bool = False
    description: str | None = None


class ReferenceTask(BaseModel):
    raw_statement: str
    template: str
    slots: list[Slot]
    answer_formula: str
    original_answer: str | None = None
    topic: str
    subject: str = "математика"
    grade: int | None = None
    difficulty_baseline: int = Field(ge=1, le=5, default=3)


class GeneratedVariant(BaseModel):
    number: int
    statement: str
    slot_values: dict[str, Any]
    answer: str
    solution: str | None = None
    difficulty: int = Field(ge=1, le=5, default=3)
    sympy_verified: bool = False
    issues: list[str] = Field(default_factory=list)


class VariantSet(BaseModel):
    id: str
    reference: ReferenceTask
    variants: list[GeneratedVariant]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnalyzeRequest(BaseModel):
    raw_statement: str
    subject: str = "математика"
    grade: int | None = None


class GenerateVariantsRequest(BaseModel):
    reference: ReferenceTask
    count: int = 4


# ---------- Конструктор контрольной из блоков ----------


class BlockSpec(BaseModel):
    """Один блок будущей контрольной: тема + класс + сколько таких задач в варианте."""
    topic: str
    grade: int = Field(ge=1, le=11)
    tasks_per_variant: int = Field(ge=1, le=10, default=1)
    subject: str = "математика"


class ComposeRequest(BaseModel):
    blocks: list[BlockSpec]
    variants_count: int = Field(ge=1, le=20, default=4)


class CompositeBlock(BaseModel):
    """Один блок результата: эталон + сгенерированные задачи, сгруппированные по вариантам."""
    topic: str
    grade: int
    tasks_per_variant: int
    subject: str = "математика"
    reference: ReferenceTask
    # variant_tasks[v] = список задач этого блока для варианта v (длиной tasks_per_variant)
    variant_tasks: list[list[GeneratedVariant]]


class CompositeAssignment(BaseModel):
    id: str
    blocks: list[CompositeBlock]
    variants_count: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
