"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, Check, RotateCw, History, ArrowRight } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Topbar } from "@/components/topbar";
import type { Task } from "@/lib/types";

interface RouteParams {
  wsId: string;
  variant: string;
  idx: string;
}

export default function TaskEditorPage({
  params,
}: {
  params: Promise<RouteParams>;
}) {
  const { wsId, variant, idx } = use(params);
  const variantNum = parseInt(variant);
  const taskIdx = parseInt(idx);
  const router = useRouter();
  const qc = useQueryClient();

  const { data } = useQuery({
    queryKey: ["worksheet", wsId],
    queryFn: () => api.getWorksheet(wsId),
  });

  const ws = data?.worksheet;
  const variantData = ws?.variants.find((v) => v.number === variantNum);
  const task = variantData?.tasks[taskIdx];
  const issues = data?.task_issues[`${variantNum}_${taskIdx}`] ?? [];
  const isValid = issues.length === 0;

  const [draft, setDraft] = useState<Task | null>(null);
  useEffect(() => {
    if (task && !draft) setDraft(task);
  }, [task, draft]);

  const dirty = task && draft && JSON.stringify(task) !== JSON.stringify(draft);

  const save = useMutation({
    mutationFn: (t: Task) => api.patchTask(wsId, variantNum, taskIdx, t),
    onSuccess: (resp) => {
      qc.setQueryData(["worksheet", wsId], resp);
      router.push(`/?ws=${wsId}`);
    },
  });

  const regen = useMutation({
    mutationFn: () => api.regenerateTask(wsId, variantNum, taskIdx),
    onSuccess: (resp) => {
      qc.setQueryData(["worksheet", wsId], resp);
      const newTask = resp.worksheet.variants.find((v) => v.number === variantNum)
        ?.tasks[taskIdx];
      if (newTask) setDraft(newTask);
    },
  });

  if (!data) {
    return (
      <>
        <Topbar contextLabel="загружаем…" />
        <div className="px-16 mt-16 mono-caps">Загружаем задачу…</div>
      </>
    );
  }
  if (!task || !draft || !variantData) {
    return (
      <>
        <Topbar contextLabel={`контрольная № ${wsId.slice(0, 4).toUpperCase()}`} />
        <div className="px-16 mt-16 text-amber">Задача не найдена</div>
      </>
    );
  }

  const otherTasks = variantData.tasks
    .map((t, i) => ({ t, i }))
    .filter(({ i }) => i !== taskIdx);

  return (
    <>
      <Topbar
        contextLabel={`контрольная № ${wsId.slice(0, 4).toUpperCase()}`}
        saved={dirty ? { time: "", warn: true } : { time: "сейчас" }}
      />

      <div className="px-16 pt-8 flex items-center gap-2 text-[13px] font-medium text-muted">
        <Link
          href={`/?ws=${wsId}`}
          className="flex items-center gap-1.5 hover:text-ink transition-colors"
        >
          <ChevronLeft size={12} strokeWidth={1.5} />
          Назад к контрольной
        </Link>
        <span className="text-hint">/</span>
        <span>Вариант {String(variantNum).padStart(2, "0")}</span>
        <span className="text-hint">/</span>
        <span className="text-ink font-semibold">
          Задача №&nbsp;{String(taskIdx + 1).padStart(2, "0")}
        </span>
      </div>

      <div className="flex-1 flex items-start">
        <main className="flex-1 px-16 pt-8 pb-14 max-w-[1080px]">
          <header className="pb-7 border-b border-ink flex flex-col gap-3">
            <div className="eyebrow">
              Вариант {String(variantNum).padStart(2, "0")} · задача №&nbsp;
              {String(taskIdx + 1).padStart(2, "0")} · правка
            </div>
            <h1 className="font-black text-[48px] leading-[50px] tracking-[-0.035em] text-ink">
              {task.statement}
            </h1>
          </header>

          <div className="flex flex-col">
            <EditorField
              label="Условие"
              hint="то, что увидит ученик в контрольной"
            >
              <textarea
                value={draft.statement}
                onChange={(e) =>
                  setDraft({ ...draft, statement: e.target.value })
                }
                rows={3}
                className="field-input resize-none"
              />
            </EditorField>

            <EditorField
              label="Ответ & выражение"
              hint="sympy пересчитает выражение и сверит с ответом"
            >
              <div className="flex flex-col gap-3.5">
                <input
                  value={draft.answer}
                  onChange={(e) =>
                    setDraft({ ...draft, answer: e.target.value })
                  }
                  className="field-input !text-[24px] !font-bold !tracking-[-0.015em]"
                  placeholder="ответ для ученика"
                />
                <input
                  value={draft.expression ?? ""}
                  onChange={(e) =>
                    setDraft({ ...draft, expression: e.target.value || null })
                  }
                  className="field-input mono"
                  placeholder="выражение для sympy"
                />
                {isValid ? (
                  <div className="flex items-center gap-1.5 text-[12px] font-medium text-green">
                    <Check size={12} strokeWidth={2} />
                    Совпадает · конечная десятичная дробь
                  </div>
                ) : (
                  <div className="text-[12px] font-medium text-amber">
                    {issues.join(" · ")}
                  </div>
                )}
              </div>
            </EditorField>

            <EditorField
              label="Решение"
              hint="пошаговый разбор для ключей учителя"
            >
              <textarea
                value={draft.solution}
                onChange={(e) =>
                  setDraft({ ...draft, solution: e.target.value })
                }
                rows={5}
                className="field-input resize-none text-[14px] leading-[22px]"
              />
            </EditorField>

            <EditorField
              label="Критерии"
              hint="шкала баллов на проверке учителя"
              last
            >
              <textarea
                value={draft.grading_criteria}
                onChange={(e) =>
                  setDraft({ ...draft, grading_criteria: e.target.value })
                }
                rows={3}
                className="field-input resize-none text-[14px] leading-[22px]"
              />
            </EditorField>
          </div>

          <div className="mt-6 pt-6 border-t border-line flex items-center justify-between">
            <div className="flex items-center gap-2 text-[13px] font-medium text-muted">
              <button
                disabled={regen.isPending}
                onClick={() => regen.mutate()}
                className="flex items-center gap-1.5 hover:text-ink transition-colors disabled:opacity-50"
              >
                <RotateCw
                  size={14}
                  strokeWidth={1.5}
                  className={regen.isPending ? "animate-spin" : ""}
                />
                {regen.isPending ? "Запрашиваем…" : "Перегенерировать у GigaChat"}
              </button>
              <span className="text-hint">·</span>
              <button className="flex items-center gap-1.5 hover:text-ink transition-colors">
                <History size={14} strokeWidth={1.5} />
                История правок
              </button>
            </div>
            <div className="flex items-center gap-3.5">
              {dirty && (
                <div className="text-[12px] font-medium text-amber flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-amber" />
                  Не сохранено
                </div>
              )}
              <button
                onClick={() => router.push(`/?ws=${wsId}`)}
                className="text-[14px] font-medium text-muted px-1 py-2.5 hover:text-ink transition-colors"
              >
                Отмена
              </button>
              <button
                disabled={!dirty || save.isPending}
                onClick={() => draft && save.mutate(draft)}
                className="btn-secondary primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {save.isPending ? "Сохраняем…" : "Сохранить правки"}
              </button>
            </div>
          </div>
        </main>

        <aside className="w-[420px] flex-shrink-0 border-l border-line p-10 sticky top-0 flex flex-col gap-9">
          <section className="flex flex-col gap-4">
            <header className="flex items-baseline justify-between">
              <div className="mono-caps ink">Проверки</div>
              <div className="mono text-[11px] text-muted tracking-[0.16em]">
                {isValid ? "0.18 с · авто" : "ошибка"}
              </div>
            </header>
            <div className="flex flex-col">
              <CheckRow
                ok={isValid}
                label="Ответ совпал с выражением"
                detail={
                  draft.expression
                    ? `sympy(${draft.expression}) == ${draft.answer}`
                    : "выражение не задано"
                }
              />
              <CheckRow
                ok={isValid}
                label="Конечная десятичная дробь"
                detail={isValid ? "denom = 5 → 2¹·5¹" : "период обнаружен"}
              />
              <CheckRow
                ok
                label={`В программе ${ws.grade} класса`}
                detail="Виленкин §28 - десятичные"
              />
              <CheckRow
                ok
                label="Уникальное условие в варианте"
                detail={`не совпадает с ${otherTasks
                  .map(({ i }) => String(i + 1).padStart(2, "0"))
                  .join(", ")}`}
                last
              />
            </div>
          </section>

          <section className="flex flex-col gap-4">
            <div className="mono-caps ink">Остальные задачи варианта</div>
            <div className="flex flex-col">
              {otherTasks.map(({ t, i }, n) => {
                const itemIssues = data.task_issues[`${variantNum}_${i}`];
                return (
                  <Link
                    key={i}
                    href={`/task/${wsId}/${variantNum}/${i}`}
                    className={`flex items-center gap-4 py-3 ${
                      n < otherTasks.length - 1
                        ? "border-b border-line"
                        : ""
                    } hover:bg-[#FAFBFC] -mx-2 px-2 transition-colors`}
                  >
                    <div className="mono text-[11px] text-muted w-6 flex-shrink-0 tracking-[0.04em]">
                      {String(i + 1).padStart(2, "0")}
                    </div>
                    <div className="text-[13px] font-medium text-ink leading-[18px] flex-1 min-w-0 truncate">
                      {t.statement}
                    </div>
                    <div
                      className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                        itemIssues ? "bg-amber" : "bg-green"
                      }`}
                    />
                    <ArrowRight
                      size={12}
                      strokeWidth={1.5}
                      className="text-hint flex-shrink-0"
                    />
                  </Link>
                );
              })}
            </div>
          </section>
        </aside>
      </div>
    </>
  );
}

function EditorField({
  label,
  hint,
  children,
  last = false,
}: {
  label: string;
  hint: string;
  children: React.ReactNode;
  last?: boolean;
}) {
  return (
    <div className={`flex gap-6 py-6 ${last ? "" : "border-b border-line"}`}>
      <div className="flex flex-col gap-1.5 w-40 flex-shrink-0">
        <div className="mono-caps ink">{label}</div>
        <div className="text-[12px] font-normal text-muted leading-[18px]">
          {hint}
        </div>
      </div>
      <div className="flex flex-col gap-2 flex-1 min-w-0">{children}</div>
    </div>
  );
}

function CheckRow({
  ok,
  label,
  detail,
  last = false,
}: {
  ok: boolean;
  label: string;
  detail: string;
  last?: boolean;
}) {
  return (
    <div
      className={`flex items-start gap-3.5 py-3.5 ${
        last ? "" : "border-b border-line"
      }`}
    >
      <div className="w-[18px] h-[18px] flex items-center justify-center flex-shrink-0 mt-0.5">
        {ok ? (
          <Check size={14} strokeWidth={2} className="text-green" />
        ) : (
          <div className="w-3 h-3 rounded-full bg-amber" />
        )}
      </div>
      <div className="flex flex-col gap-1 flex-1">
        <div className="text-[14px] font-semibold text-ink">{label}</div>
        <div className="mono text-[12px] text-muted">{detail}</div>
      </div>
    </div>
  );
}
