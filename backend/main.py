"""FastAPI бэкенд для «Сверки». In-memory store с UUID, CORS открыт для Next.js."""
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.exporters.docx_exporter import (
    assignment_docx_students,
    assignment_docx_teacher,
    students_docx_bytes,
    teacher_docx_bytes,
    variants_docx_students,
    variants_docx_teacher,
)
from backend.library import Library, LibraryItem, load_library, search_library
from backend.llm.analyzer import AnalyzeError, analyze_reference
from backend.llm.generator import (
    GenerationError,
    GenerationStats,
    generate_worksheet,
    regenerate_task,
)
from backend.models import (
    AnalyzeRequest,
    BlockSpec,
    CompositeAssignment,
    CompositeBlock,
    ComposeRequest,
    GenerateVariantsRequest,
    GenerationRequest,
    ReferenceTask,
    Task,
    VariantSet,
    WorkSheet,
)
from backend.storage import save_worksheet
from backend.validators.math_validator import validate_task_math
from backend.variant_generator import VariantGenerationError, generate_variants

app = FastAPI(title="Сверка - API")

# CORS: разрешаем фронт на localhost:3000 и любой Vercel-домен
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
EXTRA_ORIGIN = os.getenv("FRONTEND_ORIGIN")
if EXTRA_ORIGIN:
    ALLOWED_ORIGINS.append(EXTRA_ORIGIN)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store: {worksheet_id: (worksheet, stats)}
WORKSHEETS: dict[str, tuple[WorkSheet, GenerationStats]] = {}

# Case 4 in-memory store: {variant_set_id: VariantSet}
VARIANT_SETS: dict[str, VariantSet] = {}

# Сборки из нескольких блоков: {assignment_id: CompositeAssignment}
COMPOSITE_ASSIGNMENTS: dict[str, CompositeAssignment] = {}

# Библиотека эталонных задач (грузится один раз при старте)
LIBRARY: Library = load_library()


# ------- pydantic-схемы для API -------


class StatsOut(BaseModel):
    total_tasks: int
    first_pass_ok: int
    regenerated: int
    failed_after_regen: int
    duplicates_replaced: int
    elapsed_seconds: float
    issues: list[str]
    first_pass_rate: float

    @classmethod
    def from_stats(cls, s: GenerationStats) -> "StatsOut":
        return cls(
            total_tasks=s.total_tasks,
            first_pass_ok=s.first_pass_ok,
            regenerated=s.regenerated,
            failed_after_regen=s.failed_after_regen,
            duplicates_replaced=s.duplicates_replaced,
            elapsed_seconds=s.elapsed_seconds,
            issues=s.issues,
            first_pass_rate=s.first_pass_rate,
        )


class WorksheetOut(BaseModel):
    id: str
    worksheet: WorkSheet
    stats: StatsOut
    task_issues: dict[str, list[str]]  # "{variant_no}_{task_idx}" -> issues


def _validate_all(ws: WorkSheet) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for v in ws.variants:
        for i, t in enumerate(v.tasks):
            issues = validate_task_math(t)
            if issues:
                out[f"{v.number}_{i}"] = issues
    return out


def _pack(ws_id: str) -> WorksheetOut:
    ws, stats = WORKSHEETS[ws_id]
    return WorksheetOut(
        id=ws_id,
        worksheet=ws,
        stats=StatsOut.from_stats(stats),
        task_issues=_validate_all(ws),
    )


# ------- эндпоинты -------


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "worksheets": len(WORKSHEETS)}


@app.post("/generate", response_model=WorksheetOut)
def generate(req: GenerationRequest) -> WorksheetOut:
    try:
        ws, stats = generate_worksheet(req)
    except GenerationError as e:
        raise HTTPException(status_code=502, detail=str(e))
    ws_id = uuid4().hex[:12]
    WORKSHEETS[ws_id] = (ws, stats)
    save_worksheet(ws, f"{ws.subject}_{ws.grade}_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}")
    return _pack(ws_id)


@app.get("/worksheets/{ws_id}", response_model=WorksheetOut)
def get_worksheet(ws_id: str) -> WorksheetOut:
    if ws_id not in WORKSHEETS:
        raise HTTPException(status_code=404, detail="worksheet not found")
    return _pack(ws_id)


class RegenTaskBody(BaseModel):
    variant_number: int
    task_index: int
    reason: str = "ручной запрос пользователя"


@app.post("/worksheets/{ws_id}/regenerate_task", response_model=WorksheetOut)
def regen_task(ws_id: str, body: RegenTaskBody) -> WorksheetOut:
    if ws_id not in WORKSHEETS:
        raise HTTPException(status_code=404, detail="worksheet not found")
    ws, stats = WORKSHEETS[ws_id]
    try:
        regenerate_task(ws, body.variant_number, body.task_index, body.reason)
    except (ValueError, GenerationError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _pack(ws_id)


class TaskPatchBody(BaseModel):
    variant_number: int
    task_index: int
    task: Task


@app.put("/worksheets/{ws_id}/task", response_model=WorksheetOut)
def patch_task(ws_id: str, body: TaskPatchBody) -> WorksheetOut:
    if ws_id not in WORKSHEETS:
        raise HTTPException(status_code=404, detail="worksheet not found")
    ws, _ = WORKSHEETS[ws_id]
    variant = next((v for v in ws.variants if v.number == body.variant_number), None)
    if variant is None or not (0 <= body.task_index < len(variant.tasks)):
        raise HTTPException(status_code=400, detail="task not found")
    variant.tasks[body.task_index] = body.task
    return _pack(ws_id)


def _docx_response(filename: str, data: bytes) -> Response:
    from urllib.parse import quote

    # RFC 5987: имя файла может содержать не-ASCII (кириллицу) - кодируем UTF-8
    ascii_fallback = filename.encode("ascii", "ignore").decode("ascii") or "variants.docx"
    encoded = quote(filename, safe="")
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded}'
            )
        },
    )


@app.get("/worksheets/{ws_id}/students.docx")
def download_students(ws_id: str) -> Response:
    if ws_id not in WORKSHEETS:
        raise HTTPException(status_code=404)
    ws, _ = WORKSHEETS[ws_id]
    return _docx_response(f"{ws.subject}_{ws.grade}_варианты.docx", students_docx_bytes(ws))


@app.get("/worksheets/{ws_id}/teacher.docx")
def download_teacher(ws_id: str) -> Response:
    if ws_id not in WORKSHEETS:
        raise HTTPException(status_code=404)
    ws, _ = WORKSHEETS[ws_id]
    return _docx_response(f"{ws.subject}_{ws.grade}_ключи.docx", teacher_docx_bytes(ws))


# ------- Case 4: эталон → слоты → варианты -------


@app.post("/analyze", response_model=ReferenceTask)
def analyze(req: AnalyzeRequest) -> ReferenceTask:
    try:
        return analyze_reference(req.raw_statement, subject=req.subject, grade=req.grade)
    except AnalyzeError as e:
        raise HTTPException(status_code=502, detail=str(e))


class VariantSetOut(BaseModel):
    id: str
    variant_set: VariantSet


@app.post("/generate-variants", response_model=VariantSetOut)
def generate_variants_endpoint(req: GenerateVariantsRequest) -> VariantSetOut:
    try:
        variants = generate_variants(req.reference, count=req.count)
    except VariantGenerationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    vs_id = uuid4().hex[:12]
    vs = VariantSet(id=vs_id, reference=req.reference, variants=variants)
    VARIANT_SETS[vs_id] = vs
    return VariantSetOut(id=vs_id, variant_set=vs)


@app.get("/variant-sets/{vs_id}", response_model=VariantSetOut)
def get_variant_set(vs_id: str) -> VariantSetOut:
    if vs_id not in VARIANT_SETS:
        raise HTTPException(status_code=404, detail="variant set not found")
    return VariantSetOut(id=vs_id, variant_set=VARIANT_SETS[vs_id])


def _vs_filename(vs: VariantSet, suffix: str) -> str:
    topic = vs.reference.topic.replace(" ", "_")[:40]
    grade = vs.reference.grade or 0
    return f"варианты_{topic}_кл{grade}_{suffix}.docx"


@app.get("/variant-sets/{vs_id}/students.docx")
def variants_download_students(vs_id: str) -> Response:
    if vs_id not in VARIANT_SETS:
        raise HTTPException(status_code=404)
    vs = VARIANT_SETS[vs_id]
    return _docx_response(_vs_filename(vs, "ученики"), variants_docx_students(vs))


@app.get("/variant-sets/{vs_id}/teacher.docx")
def variants_download_teacher(vs_id: str) -> Response:
    if vs_id not in VARIANT_SETS:
        raise HTTPException(status_code=404)
    vs = VARIANT_SETS[vs_id]
    return _docx_response(_vs_filename(vs, "ключи"), variants_docx_teacher(vs))


# ------- Библиотека эталонов -------


class LibraryOut(BaseModel):
    version: str
    description: str
    items: list[LibraryItem]


@app.get("/library", response_model=LibraryOut)
def library_get(
    query: str | None = None,
    grade: int | None = None,
    subject: str | None = None,
    combined_only: bool = False,
) -> LibraryOut:
    items = search_library(
        LIBRARY, query=query, grade=grade, subject=subject, combined_only=combined_only
    )
    return LibraryOut(version=LIBRARY.version, description=LIBRARY.description, items=items)


# ------- Быстрая генерация: тема + класс + количество → варианты -------


class QuickGenerateRequest(BaseModel):
    topic: str
    grade: int = 5
    count: int = 4


def _resolve_reference_for_block(spec: BlockSpec) -> ReferenceTask:
    """Найти в библиотеке эталон по теме+классу+предмету, проанализировать через LLM."""
    candidates = search_library(
        LIBRARY, query=spec.topic, grade=spec.grade, subject=spec.subject
    )
    if not candidates:
        # ослабляем сначала по grade, потом по subject
        candidates = search_library(LIBRARY, query=spec.topic, subject=spec.subject)
    if not candidates:
        candidates = search_library(LIBRARY, query=spec.topic)
    if not candidates:
        raise HTTPException(
            status_code=404,
            detail=(
                f"тема «{spec.topic}» ({spec.subject}, класс {spec.grade}) "
                f"не найдена в библиотеке"
            ),
        )
    candidates.sort(key=lambda i: (abs(i.grade - spec.grade), i.grade))
    chosen = candidates[0]
    try:
        return analyze_reference(chosen.statement, subject=spec.subject, grade=spec.grade)
    except AnalyzeError as e:
        raise HTTPException(status_code=502, detail=f"анализ эталона «{spec.topic}»: {e}")


class AssignmentOut(BaseModel):
    id: str
    assignment: CompositeAssignment


@app.post("/compose-assignment", response_model=AssignmentOut)
def compose_assignment(req: ComposeRequest) -> AssignmentOut:
    """Собрать контрольную из нескольких блоков (разные темы / классы)."""
    if not req.blocks:
        raise HTTPException(status_code=400, detail="нужен хотя бы один блок")

    blocks_out: list[CompositeBlock] = []
    for spec in req.blocks:
        ref = _resolve_reference_for_block(spec)
        total_needed = req.variants_count * spec.tasks_per_variant
        try:
            tasks = generate_variants(ref, count=total_needed)
        except VariantGenerationError as e:
            raise HTTPException(
                status_code=422,
                detail=f"блок «{spec.topic}» (класс {spec.grade}): {e}",
            )
        # разрезаем плоский список на варианты по tasks_per_variant штук
        variant_tasks: list[list[GeneratedVariant]] = []
        for v in range(req.variants_count):
            start = v * spec.tasks_per_variant
            end = start + spec.tasks_per_variant
            variant_tasks.append(tasks[start:end])
        blocks_out.append(
            CompositeBlock(
                topic=spec.topic,
                grade=spec.grade,
                tasks_per_variant=spec.tasks_per_variant,
                subject=spec.subject,
                reference=ref,
                variant_tasks=variant_tasks,
            )
        )

    aid = uuid4().hex[:12]
    assignment = CompositeAssignment(
        id=aid,
        blocks=blocks_out,
        variants_count=req.variants_count,
    )
    COMPOSITE_ASSIGNMENTS[aid] = assignment
    return AssignmentOut(id=aid, assignment=assignment)


@app.get("/assignments/{aid}", response_model=AssignmentOut)
def get_assignment(aid: str) -> AssignmentOut:
    if aid not in COMPOSITE_ASSIGNMENTS:
        raise HTTPException(status_code=404, detail="контрольная не найдена")
    return AssignmentOut(id=aid, assignment=COMPOSITE_ASSIGNMENTS[aid])


def _assignment_filename(a: CompositeAssignment, suffix: str) -> str:
    topics = "_".join(b.topic.replace(" ", "_")[:20] for b in a.blocks[:3])
    return f"контрольная_{topics}_{suffix}.docx"


@app.get("/assignments/{aid}/students.docx")
def assignment_download_students(aid: str) -> Response:
    if aid not in COMPOSITE_ASSIGNMENTS:
        raise HTTPException(status_code=404)
    a = COMPOSITE_ASSIGNMENTS[aid]
    return _docx_response(_assignment_filename(a, "ученики"), assignment_docx_students(a))


@app.get("/assignments/{aid}/teacher.docx")
def assignment_download_teacher(aid: str) -> Response:
    if aid not in COMPOSITE_ASSIGNMENTS:
        raise HTTPException(status_code=404)
    a = COMPOSITE_ASSIGNMENTS[aid]
    return _docx_response(_assignment_filename(a, "ключи"), assignment_docx_teacher(a))


@app.post("/quick-generate", response_model=VariantSetOut)
def quick_generate(req: QuickGenerateRequest) -> VariantSetOut:
    """Учитель указывает только тему + класс + количество.
    Бэкенд сам подбирает эталонную задачу из библиотеки, анализирует её и генерирует N вариантов.
    """
    # 1. Ищем эталон в библиотеке: тема + класс (если ровно по классу нет, расширяем поиск)
    candidates = search_library(LIBRARY, query=req.topic, grade=req.grade)
    if not candidates:
        candidates = search_library(LIBRARY, query=req.topic)
    if not candidates:
        raise HTTPException(
            status_code=404,
            detail=(
                f"не нашли эталон по теме «{req.topic}» для класса {req.grade}. "
                "попробуй другое название или загляни в библиотеку эталонов"
            ),
        )

    # Приоритет: ровно тот же класс, потом ближайший по уровню
    candidates.sort(key=lambda i: (abs(i.grade - req.grade), i.grade))
    chosen = candidates[0]

    # 2. Анализируем эталон
    try:
        ref = analyze_reference(chosen.statement, subject="математика", grade=req.grade)
    except AnalyzeError as e:
        raise HTTPException(status_code=502, detail=f"анализ эталона не удался: {e}")

    # 3. Генерируем варианты
    try:
        variants = generate_variants(ref, count=req.count)
    except VariantGenerationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    vs_id = uuid4().hex[:12]
    vs = VariantSet(id=vs_id, reference=ref, variants=variants)
    VARIANT_SETS[vs_id] = vs
    return VariantSetOut(id=vs_id, variant_set=vs)
