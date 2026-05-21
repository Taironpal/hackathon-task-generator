"use client";

import { ArrowRight } from "lucide-react";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { GenerationRequest } from "@/lib/types";

const AUDIENCES: Array<{
  id: "standard" | "weak" | "strong";
  label: string;
}> = [
  { id: "standard", label: "Стандартный класс" },
  { id: "weak", label: "Базовый - для отстающих" },
  { id: "strong", label: "Продвинутый - для сильных" },
];

const VARIANTS_RANGE = [2, 3, 4, 5, 6, 8] as const;
const TASKS_RANGE = [3, 4, 5, 6, 7, 8] as const;
const DIFFICULTY_RANGE = [1, 2, 3, 4, 5] as const;

interface Props {
  defaultTopic?: string;
}

export function ParamRail({ defaultTopic = "Сложение и вычитание десятичных дробей" }: Props) {
  const router = useRouter();
  const [grade, setGrade] = useState(5);
  const [topic, setTopic] = useState(defaultTopic);
  const [variants, setVariants] = useState(4);
  const [tasks, setTasks] = useState(5);
  const [difficulty, setDifficulty] = useState(3);
  const [audience, setAudience] = useState<"standard" | "weak" | "strong">("standard");
  const [notes, setNotes] = useState("");

  const generate = useMutation({
    mutationFn: (req: GenerationRequest) => api.generate(req),
    onSuccess: (data) => router.push(`/?ws=${data.id}`),
  });

  return (
    <div className="flex flex-col gap-7">
      <div>
        <div className="mono-caps ink mb-1.5">Параметры</div>
        <div className="text-[22px] font-bold tracking-[-0.02em]">
          Опишите контрольную
        </div>
      </div>

      <div className="flex flex-col">
        <Field label="Тема">
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="text-[16px] font-semibold tracking-[-0.01em] text-ink bg-transparent border-0 outline-none p-0 w-full"
            placeholder="Например: Умножение десятичных дробей"
          />
        </Field>

        <Field label="Класс" inline>
          <NumStepper
            value={grade}
            options={[3, 4, 5, 6, 7, 8]}
            onChange={setGrade}
          />
        </Field>

        <Field label="Вариантов" inline>
          <NumStepper
            value={variants}
            options={[...VARIANTS_RANGE]}
            onChange={setVariants}
          />
        </Field>

        <Field label="Задач в варианте" inline>
          <NumStepper
            value={tasks}
            options={[...TASKS_RANGE]}
            onChange={setTasks}
          />
        </Field>

        <Field label="Сложность" inline>
          <NumStepper
            value={difficulty}
            options={[...DIFFICULTY_RANGE]}
            onChange={setDifficulty}
          />
        </Field>

        <div className="py-[18px] border-b border-line flex flex-col gap-2.5">
          <div className="text-[12px] font-medium text-muted">Аудитория</div>
          <div className="flex flex-col">
            {AUDIENCES.map((a) => (
              <button
                key={a.id}
                onClick={() => setAudience(a.id)}
                className="flex items-center gap-2.5 py-2 text-left"
              >
                <div
                  className={`w-3.5 h-3.5 rounded-full border-[1.5px] flex items-center justify-center flex-shrink-0 ${
                    audience === a.id ? "bg-ink border-ink" : "border-hint"
                  }`}
                >
                  {audience === a.id && (
                    <div className="w-[5px] h-[5px] rounded-full bg-white" />
                  )}
                </div>
                <div
                  className={`text-[14px] ${
                    audience === a.id
                      ? "font-semibold text-ink"
                      : "font-medium text-muted"
                  }`}
                >
                  {a.label}
                </div>
              </button>
            ))}
          </div>
        </div>

        <Field label="Уточнения">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Например: только текстовые задачи"
            rows={2}
            className="resize-none text-[14px] text-ink bg-transparent border-0 outline-none p-0 w-full placeholder:text-hint"
          />
        </Field>
      </div>

      <div className="flex flex-col gap-3">
        <button
          className="btn-primary"
          disabled={generate.isPending || !topic.trim()}
          onClick={() =>
            generate.mutate({
              subject: "математика",
              grade,
              topic,
              variants_count: variants,
              tasks_per_variant: tasks,
              difficulty,
              audience,
              notes: notes.trim() || null,
            })
          }
        >
          <span>{generate.isPending ? "Генерируем…" : "Сгенерировать"}</span>
          <ArrowRight size={16} strokeWidth={1.8} />
        </button>
        {generate.isError && (
          <div className="text-[12px] font-medium text-amber leading-tight">
            {(generate.error as Error).message}
          </div>
        )}
        <div className="text-[12px] font-normal text-muted leading-[18px]">
          ~28&nbsp;секунд работы GigaChat. Каждый ответ перепроверит sympy - задачи
          с&nbsp;ошибками не&nbsp;попадут в&nbsp;файл.
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  children,
  inline = false,
}: {
  label: string;
  children: React.ReactNode;
  inline?: boolean;
}) {
  return (
    <div
      className={`py-[18px] border-b border-line ${
        inline ? "flex items-baseline justify-between" : "flex flex-col gap-1.5"
      }`}
    >
      <div className="text-[12px] font-medium text-muted">{label}</div>
      {children}
    </div>
  );
}

function NumStepper({
  value,
  options,
  onChange,
}: {
  value: number;
  options: number[];
  onChange: (n: number) => void;
}) {
  return (
    <div className="num-stepper">
      {options.map((n) => (
        <button
          key={n}
          onClick={() => onChange(n)}
          className={n === value ? "active" : ""}
        >
          {n}
        </button>
      ))}
    </div>
  );
}
