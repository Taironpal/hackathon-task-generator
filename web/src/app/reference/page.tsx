"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Check,
  ChevronRight,
  Download,
  Loader2,
  Plus,
  Sparkles,
  X,
} from "lucide-react";
import { useSearchParams } from "next/navigation";
import { Suspense, useMemo, useState } from "react";
import { Topbar } from "@/components/topbar";
import { api } from "@/lib/api";
import type {
  AssignmentOut,
  BlockSpec,
  CompositeAssignment,
  CompositeBlock,
  GeneratedVariant,
} from "@/lib/types";

type Stage = "form" | "result";

interface BlockDraft extends BlockSpec {
  uid: string;
}

const SUBJECTS: { value: string; label: string }[] = [
  { value: "математика", label: "математика" },
  { value: "физика", label: "физика" },
  { value: "химия", label: "химия" },
  { value: "информатика", label: "информатика" },
];

const INITIAL_BLOCK: BlockDraft = {
  uid: "b-initial",
  topic: "",
  grade: 5,
  tasks_per_variant: 1,
  subject: "математика",
};

// uid генерится только при добавлении новых блоков — это уже клиент, нет SSR-конфликта
let _blockCounter = 1;
function newBlock(grade = 5, subject = "математика"): BlockDraft {
  _blockCounter += 1;
  return {
    uid: `b-${_blockCounter}`,
    topic: "",
    grade,
    tasks_per_variant: 1,
    subject,
  };
}

export default function ReferencePage() {
  return (
    <Suspense fallback={null}>
      <ReferencePageInner />
    </Suspense>
  );
}

function ReferencePageInner() {
  const searchParams = useSearchParams();
  const initialBlock = useMemo<BlockDraft>(() => {
    const topic = searchParams.get("topic");
    const gradeRaw = searchParams.get("grade");
    const subject = searchParams.get("subject");
    if (!topic && !gradeRaw && !subject) return INITIAL_BLOCK;
    const grade = gradeRaw ? Math.max(1, Math.min(11, Number(gradeRaw) || 5)) : 5;
    return {
      uid: "b-initial",
      topic: topic ?? "",
      grade,
      tasks_per_variant: 1,
      subject: subject ?? "математика",
    };
    // searchParams читается один раз — последующие изменения query не пересоздают форму
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const [blocks, setBlocks] = useState<BlockDraft[]>([initialBlock]);
  const [variantsCount, setVariantsCount] = useState<number>(4);
  const [assignment, setAssignment] = useState<CompositeAssignment | null>(null);
  const [stage, setStage] = useState<Stage>("form");

  const { data: lib } = useQuery({
    queryKey: ["library-topics"],
    queryFn: () => api.getLibrary(),
    staleTime: 60_000,
  });

  const topicOptions = useMemo(() => {
    if (!lib)
      return [] as { topic: string; grades: number[]; subjects: string[] }[];
    const map = new Map<
      string,
      { grades: Set<number>; subjects: Set<string> }
    >();
    for (const it of lib.items) {
      if (!map.has(it.topic))
        map.set(it.topic, { grades: new Set(), subjects: new Set() });
      map.get(it.topic)!.grades.add(it.grade);
      map.get(it.topic)!.subjects.add(it.subject);
    }
    return [...map.entries()]
      .map(([t, v]) => ({
        topic: t,
        grades: [...v.grades].sort((a, b) => a - b),
        subjects: [...v.subjects],
      }))
      .sort((a, b) => a.topic.localeCompare(b.topic, "ru"));
  }, [lib]);

  const compose = useMutation({
    mutationFn: (): Promise<AssignmentOut> =>
      api.composeAssignment({
        blocks: blocks.map(({ uid, ...rest }) => rest),
        variants_count: variantsCount,
      }),
    onSuccess: (resp) => {
      setAssignment(resp.assignment);
      setStage("result");
    },
  });

  const updateBlock = (uid: string, patch: Partial<BlockSpec>) => {
    setBlocks((bs) => bs.map((b) => (b.uid === uid ? { ...b, ...patch } : b)));
  };

  const addBlock = () => {
    const lastGrade = blocks[blocks.length - 1]?.grade ?? 5;
    setBlocks((bs) => [...bs, newBlock(lastGrade)]);
  };

  const removeBlock = (uid: string) => {
    setBlocks((bs) => (bs.length === 1 ? bs : bs.filter((b) => b.uid !== uid)));
  };

  const reset = () => {
    setBlocks([INITIAL_BLOCK]);
    setVariantsCount(4);
    setAssignment(null);
    setStage("form");
    compose.reset();
  };

  return (
    <>
      <Topbar
        contextLabel={
          stage === "result" ? "готовая контрольная" : "конструктор контрольной"
        }
      />
      <main className="flex-1 px-5 sm:px-10 lg:px-12 pt-6 sm:pt-8 pb-32 max-w-[1080px] mx-auto w-full">
        {stage === "form" && (
          <ComposerForm
            blocks={blocks}
            variantsCount={variantsCount}
            setVariantsCount={setVariantsCount}
            topicOptions={topicOptions}
            updateBlock={updateBlock}
            addBlock={addBlock}
            removeBlock={removeBlock}
            isLoading={compose.isPending}
            error={compose.error}
            onSubmit={() => compose.mutate()}
          />
        )}

        {stage === "result" && assignment && (
          <AssignmentResult
            assignment={assignment}
            onReset={reset}
            onRegenerate={() => compose.mutate()}
            isRegenerating={compose.isPending}
          />
        )}
      </main>
    </>
  );
}

// ============================================================
// Конструктор: блоки разных тем
// ============================================================

interface ComposerProps {
  blocks: BlockDraft[];
  variantsCount: number;
  setVariantsCount: (v: number) => void;
  topicOptions: { topic: string; grades: number[] }[];
  updateBlock: (uid: string, patch: Partial<BlockSpec>) => void;
  addBlock: () => void;
  removeBlock: (uid: string) => void;
  isLoading: boolean;
  error: unknown;
  onSubmit: () => void;
}

function ComposerForm({
  blocks,
  variantsCount,
  setVariantsCount,
  topicOptions,
  updateBlock,
  addBlock,
  removeBlock,
  isLoading,
  error,
  onSubmit,
}: ComposerProps) {
  const tasksPerVariant = blocks.reduce((s, b) => s + b.tasks_per_variant, 0);
  const canSubmit = blocks.every((b) => b.topic.trim().length > 0);

  return (
    <div className="flex flex-col gap-6 sm:gap-7">
      <header className="flex flex-col gap-2">
        <div className="eyebrow">конструктор</div>
        <h1 className="font-black text-[26px] sm:text-[32px] lg:text-[36px] leading-[1.1] tracking-[-0.025em] text-ink max-w-[760px]">
          Соберите контрольную из&nbsp;блоков.
        </h1>
        <p className="text-[14px] text-ink-2 max-w-[680px] leading-5">
          Каждый блок&nbsp;- своя тема и&nbsp;класс. В&nbsp;каждом варианте будет указанное число задач каждого блока. Подбираем эталоны из&nbsp;программы, sympy перепроверяет ответы.
        </p>
      </header>

      <div className="flex flex-col gap-3">
        {blocks.map((b, idx) => (
          <BlockCard
            key={b.uid}
            block={b}
            index={idx}
            canRemove={blocks.length > 1}
            topicOptions={topicOptions}
            onChange={(patch) => updateBlock(b.uid, patch)}
            onRemove={() => removeBlock(b.uid)}
          />
        ))}
        <button
          type="button"
          onClick={addBlock}
          className="flex items-center justify-center gap-2 text-[14px] font-medium text-muted hover:text-ink transition-colors py-4 rounded-lg border border-dashed border-line hover:border-ink hover:bg-hair/40"
        >
          <Plus size={15} strokeWidth={1.8} />
          Добавить блок
        </button>
      </div>

      <ComposerFooter
        variantsCount={variantsCount}
        setVariantsCount={setVariantsCount}
        tasksPerVariant={tasksPerVariant}
        isLoading={isLoading}
        canSubmit={canSubmit}
        onSubmit={onSubmit}
      />

      {error ? (
        <div className="text-amber text-[13px] font-medium">
          {(error as Error).message}
        </div>
      ) : null}
    </div>
  );
}

interface FooterProps {
  variantsCount: number;
  setVariantsCount: (v: number) => void;
  tasksPerVariant: number;
  isLoading: boolean;
  canSubmit: boolean;
  onSubmit: () => void;
}

function ComposerFooter({
  variantsCount,
  setVariantsCount,
  tasksPerVariant,
  isLoading,
  canSubmit,
  onSubmit,
}: FooterProps) {
  return (
    <div className="sticky bottom-0 -mx-5 sm:-mx-10 lg:-mx-12 px-5 sm:px-10 lg:px-12 py-4 bg-white border-t border-line shadow-[0_-8px_24px_-12px_rgba(10,11,14,0.08)] flex items-center gap-3 sm:gap-5 flex-wrap">
      <label className="flex items-center gap-2">
        <span className="mono-caps">вариантов</span>
        <input
          type="number"
          min={1}
          max={20}
          value={variantsCount}
          onChange={(e) =>
            setVariantsCount(
              Math.max(1, Math.min(20, Number(e.target.value) || 1)),
            )
          }
          className="field-input !w-16 !py-1.5 !text-center !text-[14px]"
        />
      </label>
      <div className="flex items-baseline gap-1 mono-caps">
        <span>в варианте</span>
        <span className="text-ink font-bold text-[14px] tabular-nums">
          {tasksPerVariant}
        </span>
      </div>
      <div className="hidden sm:flex items-baseline gap-1 mono-caps">
        <span>всего</span>
        <span className="text-ink font-bold text-[14px] tabular-nums">
          {tasksPerVariant * variantsCount}
        </span>
      </div>
      <div className="flex-1" />
      <button
        onClick={onSubmit}
        disabled={isLoading || !canSubmit}
        className="btn-secondary primary !py-3 !px-5 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? (
          <>
            <Loader2 size={14} strokeWidth={1.6} className="animate-spin" />
            Собираем…
          </>
        ) : (
          <>
            <Sparkles size={14} strokeWidth={1.6} />
            Сгенерировать
            <ChevronRight size={14} strokeWidth={1.6} />
          </>
        )}
      </button>
    </div>
  );
}

interface BlockCardProps {
  block: BlockDraft;
  index: number;
  canRemove: boolean;
  topicOptions: { topic: string; grades: number[]; subjects: string[] }[];
  onChange: (patch: Partial<BlockSpec>) => void;
  onRemove: () => void;
}

function BlockCard({
  block,
  index,
  canRemove,
  topicOptions,
  onChange,
  onRemove,
}: BlockCardProps) {
  const popularForGrade = useMemo(
    () =>
      topicOptions
        .filter((t) => t.subjects.includes(block.subject))
        .filter((t) => t.grades.includes(block.grade))
        .slice(0, 6)
        .map((t) => t.topic),
    [topicOptions, block.grade, block.subject],
  );

  const datalistId = `topics-${block.uid}`;

  return (
    <div className="rounded-lg border border-line bg-white p-4 sm:p-5 flex flex-col gap-3.5">
      <div className="flex items-baseline justify-between gap-3">
        <div className="flex items-baseline gap-2">
          <div className="mono-caps">блок</div>
          <div className="font-black text-[18px] text-ink tabular-nums tracking-[-0.04em]">
            {String(index + 1).padStart(2, "0")}
          </div>
        </div>
        <button
          type="button"
          onClick={onRemove}
          disabled={!canRemove}
          aria-label="Удалить блок"
          className="w-7 h-7 rounded-md flex items-center justify-center text-muted hover:text-ink hover:bg-hair transition-colors disabled:opacity-30 disabled:hover:bg-transparent"
        >
          <X size={14} strokeWidth={1.6} />
        </button>
      </div>

      <div className="flex flex-wrap gap-1">
        {SUBJECTS.map((s) => (
          <button
            key={s.value}
            type="button"
            onClick={() =>
              onChange({
                subject: s.value,
                // Сбрасываем тему при смене предмета, чтобы не было «проценты» в физике
                topic: block.subject === s.value ? block.topic : "",
              })
            }
            className={`text-[11px] font-medium px-2.5 py-1 rounded-md transition-colors ${
              block.subject === s.value
                ? "bg-ink text-white"
                : "text-muted hover:text-ink border border-line hover:border-ink"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* datalist уникальный для каждой карточки — фильтруется по предмету */}
      <datalist id={datalistId}>
        {topicOptions
          .filter((t) => t.subjects.includes(block.subject))
          .map((t) => (
            <option key={t.topic} value={t.topic}>
              {`${t.grades[0]}-${t.grades[t.grades.length - 1]} кл`}
            </option>
          ))}
      </datalist>

      <div className="flex flex-col gap-2">
        <label htmlFor={`topic-${block.uid}`} className="mono-caps">
          тема
        </label>
        <input
          id={`topic-${block.uid}`}
          type="text"
          list={datalistId}
          value={block.topic}
          onChange={(e) => onChange({ topic: e.target.value })}
          placeholder={`например, ${popularForGrade[0] ?? "..."}`}
          className="field-input !py-2 !text-[15px]"
        />
        {popularForGrade.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {popularForGrade.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => onChange({ topic: t })}
                className={`text-[12px] font-medium px-2.5 py-1 rounded-md transition-colors ${
                  block.topic.trim().toLowerCase() === t.toLowerCase()
                    ? "bg-ink text-white"
                    : "text-muted hover:text-ink border border-line hover:border-ink"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 pt-1">
        <label className="flex flex-col gap-1.5">
          <span className="mono-caps">класс</span>
          <input
            type="number"
            min={1}
            max={11}
            value={block.grade}
            onChange={(e) =>
              onChange({
                grade: Math.max(1, Math.min(11, Number(e.target.value) || 5)),
              })
            }
            className="field-input !py-2 !text-center !text-[15px] !font-bold"
          />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="mono-caps">задач в&nbsp;варианте</span>
          <input
            type="number"
            min={1}
            max={10}
            value={block.tasks_per_variant}
            onChange={(e) =>
              onChange({
                tasks_per_variant: Math.max(
                  1,
                  Math.min(10, Number(e.target.value) || 1),
                ),
              })
            }
            className="field-input !py-2 !text-center !text-[15px] !font-bold"
          />
        </label>
      </div>
    </div>
  );
}

// ============================================================
// Результат: контрольная с блоками
// ============================================================

interface ResultProps {
  assignment: CompositeAssignment;
  onReset: () => void;
  onRegenerate: () => void;
  isRegenerating: boolean;
}

function AssignmentResult({
  assignment,
  onReset,
  onRegenerate,
  isRegenerating,
}: ResultProps) {
  const allTasks = useMemo(
    () =>
      assignment.blocks.flatMap((b) => b.variant_tasks.flat()),
    [assignment],
  );
  const verified = allTasks.filter((t) => t.sympy_verified).length;
  const total = allTasks.length;
  const verifiedPct = Math.round((verified / total) * 100);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex items-baseline justify-between gap-6">
        <div className="flex flex-col gap-1">
          <div className="eyebrow">готово</div>
          <h2 className="font-black text-[26px] leading-[30px] tracking-[-0.025em] text-ink">
            {assignment.blocks.map((b) => b.topic).join(" + ")}
          </h2>
          <div className="text-[12px] font-medium text-muted mt-1">
            {assignment.blocks.length} блок(ов) · {assignment.variants_count} вариантов · {total} задач
          </div>
        </div>
        <button
          onClick={onReset}
          className="mono-caps hover:text-ink transition-colors"
        >
          новая контрольная
        </button>
      </header>

      <div className="flex items-end justify-between gap-8 pb-5 border-b border-line flex-wrap">
        <div className="flex items-end gap-5">
          <div className="flex items-baseline font-black text-ink text-[68px] leading-[64px] tracking-[-0.05em] tabular-nums">
            {verifiedPct}
            <span className="font-bold text-[24px] tracking-[-0.04em]">%</span>
          </div>
          <div className="flex flex-col gap-0.5 pb-1">
            <div className="mono-caps ink">sympy ✓</div>
            <div className="text-[12px] font-medium text-ink-2 max-w-[240px] leading-4">
              {verified} из&nbsp;{total} задач сверены символьной арифметикой
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRegenerate}
            disabled={isRegenerating}
            className="btn-ghost"
          >
            {isRegenerating ? (
              <>
                <Loader2 size={13} strokeWidth={1.6} className="animate-spin" />
                Генерируем…
              </>
            ) : (
              "Перегенерировать"
            )}
          </button>
          <a
            href={api.assignmentDownloadUrl(assignment.id, "students")}
            download
            className="btn-secondary !py-2.5 !px-3.5 !text-[13px]"
          >
            <Download size={13} strokeWidth={1.6} />
            Варианты&nbsp;.docx
          </a>
          <a
            href={api.assignmentDownloadUrl(assignment.id, "teacher")}
            download
            className="btn-secondary primary !py-2.5 !px-3.5 !text-[13px]"
          >
            <Download size={13} strokeWidth={1.6} />
            Ключи&nbsp;.docx
          </a>
        </div>
      </div>

      <div className="flex flex-col gap-8">
        {Array.from({ length: assignment.variants_count }, (_, vIdx) => (
          <VariantCard
            key={vIdx}
            variantIndex={vIdx}
            blocks={assignment.blocks}
          />
        ))}
      </div>
    </div>
  );
}

function VariantCard({
  variantIndex,
  blocks,
}: {
  variantIndex: number;
  blocks: CompositeBlock[];
}) {
  let runningNumber = 0;
  return (
    <div className="border border-line rounded-lg p-5 flex flex-col gap-4">
      <div className="flex items-baseline justify-between">
        <div className="flex items-baseline gap-3">
          <div className="mono-caps">вариант</div>
          <div className="font-black text-[24px] text-ink tabular-nums tracking-[-0.04em]">
            {String(variantIndex + 1).padStart(2, "0")}
          </div>
        </div>
        <div className="mono-caps">
          {blocks.reduce((s, b) => s + b.variant_tasks[variantIndex].length, 0)} задач
        </div>
      </div>

      <div className="flex flex-col">
        {blocks.map((block, bIdx) => (
          <div
            key={bIdx}
            className="border-t border-line py-3 first:border-t-0 first:pt-0"
          >
            <div className="flex items-baseline gap-3 pb-2">
              <div className="mono-caps">блок {bIdx + 1}</div>
              <div className="text-[13px] font-semibold text-ink">
                {block.topic}
              </div>
              <div className="mono-caps">{block.grade} кл</div>
            </div>
            {block.variant_tasks[variantIndex].map((task) => {
              runningNumber += 1;
              return (
                <TaskLine
                  key={`${bIdx}-${task.number}`}
                  number={runningNumber}
                  task={task}
                />
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

function TaskLine({
  number,
  task,
}: {
  number: number;
  task: GeneratedVariant;
}) {
  return (
    <div className="flex items-start gap-4 py-2">
      <div className="font-bold text-[14px] text-ink tabular-nums w-6 flex-shrink-0 pt-0.5">
        {number}.
      </div>
      <div className="flex flex-col gap-0.5 flex-1 min-w-0">
        <div className="font-medium text-[14px] leading-[20px] text-ink">
          {task.statement}
        </div>
        <div className="flex items-baseline gap-3 text-[11px]">
          <span className="flex items-baseline gap-1">
            <span className="mono-caps">ответ</span>
            <span className="font-bold text-[13px] text-ink tabular-nums">
              {task.answer}
            </span>
          </span>
          <span className="mono text-[10px] text-muted">
            {Object.entries(task.slot_values)
              .map(([k, v]) => `${k}=${v}`)
              .join(", ")}
          </span>
        </div>
      </div>
      <div className="flex items-center gap-1 flex-shrink-0 pt-1">
        {task.sympy_verified ? (
          <>
            <Check size={11} strokeWidth={2.4} className="text-green" />
            <span className="text-[10px] font-semibold text-green">sympy</span>
          </>
        ) : (
          <>
            <div className="w-1 h-1 rounded-full bg-amber" />
            <span className="text-[10px] font-semibold text-amber">проверка</span>
          </>
        )}
      </div>
    </div>
  );
}
