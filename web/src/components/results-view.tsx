"use client";

import { Download, RotateCw, Pencil } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { WorksheetOut } from "@/lib/types";
import { api } from "@/lib/api";

interface Props {
  data: WorksheetOut;
}

export function ResultsView({ data }: Props) {
  const { worksheet: ws, stats, task_issues } = data;
  const [activeVariant, setActiveVariant] = useState(0);
  const qc = useQueryClient();
  const regen = useMutation({
    mutationFn: ({ vn, ti }: { vn: number; ti: number }) =>
      api.regenerateTask(data.id, vn, ti),
    onSuccess: (resp) => qc.setQueryData(["worksheet", data.id], resp),
  });
  const qualityPct = Math.round(stats.first_pass_rate * 100);
  const regenWord =
    stats.regenerated === 1 ? "задача регенерирована" : "задач регенерировано";

  return (
    <div className="flex flex-col">
      {/* downloads - right-aligned strip */}
      <div className="flex justify-end gap-3 mt-8">
        <a
          href={api.downloadUrl(data.id, "students")}
          className="btn-secondary"
          download
        >
          <Download size={14} strokeWidth={1.6} />
          Варианты&nbsp;.docx
        </a>
        <a
          href={api.downloadUrl(data.id, "teacher")}
          className="btn-secondary primary"
          download
        >
          <Download size={14} strokeWidth={1.6} />
          Ключи учителя&nbsp;.docx
        </a>
      </div>

      {/* heading */}
      <div className="eyebrow mt-4">
        {ws.subject}, {ws.grade}&nbsp;класс · вариантов&nbsp;{ws.variants.length}
        {" · "}задач&nbsp;{stats.total_tasks}
      </div>
      <h1 className="font-black text-[44px] leading-[48px] tracking-[-0.03em] text-ink mt-3.5">
        {ws.topic}
      </h1>

      {/* metrics */}
      <div className="mt-8 pt-8 pb-8 border-t border-ink border-b border-line flex items-end justify-between gap-16">
        <div className="flex items-end gap-6">
          <div className="flex items-baseline font-black text-ink text-[140px] leading-[120px] tracking-[-0.06em]">
            {qualityPct}
            <span className="font-bold text-[48px] tracking-[-0.04em]">%</span>
          </div>
          <div className="flex flex-col gap-1.5 pb-2">
            <div className="mono-caps ink">Качество</div>
            <div className="text-[14px] font-medium text-ink-2 max-w-[240px] leading-5">
              Задач, прошедших проверку sympy с&nbsp;первого раза
            </div>
          </div>
        </div>
        <div className="flex flex-col gap-3.5 flex-shrink-0">
          <StatRow value={`${stats.elapsed_seconds.toFixed(0)} сек`} desc="время генерации" />
          <StatRow value={`${stats.regenerated}`} desc={regenWord} />
          <StatRow
            value={`${stats.total_tasks}`}
            desc={`всего задач, ${ws.variants.length} × ${ws.variants[0]?.tasks.length ?? 0}`}
            last
          />
        </div>
      </div>

      {/* variant tabs */}
      <div className="mt-10 flex items-end gap-9 border-b border-line">
        {ws.variants.map((v, idx) => {
          const okCount = v.tasks.filter(
            (_, ti) => !task_issues[`${v.number}_${ti}`],
          ).length;
          const warnCount = v.tasks.length - okCount;
          const active = idx === activeVariant;
          return (
            <button
              key={v.number}
              onClick={() => setActiveVariant(idx)}
              className={`flex flex-col items-start gap-1.5 pb-3.5 -mb-px ${
                active ? "border-b-2 border-ink" : ""
              }`}
            >
              <div className="mono-caps">Вариант</div>
              <div className="flex items-baseline gap-2">
                <div
                  className={`font-black text-[32px] tracking-[-0.04em] ${
                    active ? "text-ink" : "text-hint font-semibold"
                  }`}
                >
                  {String(v.number).padStart(2, "0")}
                </div>
                {warnCount > 0 ? (
                  <div className="flex items-center gap-1.5 text-[12px] font-medium text-amber">
                    <div className="w-1.5 h-1.5 rounded-full bg-amber" />
                    {warnCount} на&nbsp;проверке
                  </div>
                ) : (
                  <div className="text-[12px] font-medium text-muted">
                    {okCount}/{v.tasks.length} верно
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* task list */}
      <div className="mt-2 flex flex-col">
        <div className="mono-caps py-3.5">
          Задач в&nbsp;варианте: {ws.variants[activeVariant].tasks.length}
        </div>
        {ws.variants[activeVariant].tasks.map((task, idx) => {
          const issues = task_issues[`${ws.variants[activeVariant].number}_${idx}`];
          const warn = !!issues;
          return (
            <div
              key={idx}
              className="flex items-start gap-8 py-6 border-b border-line"
            >
              <div className="flex flex-col gap-0.5 w-12 flex-shrink-0 pt-1">
                <div className="mono text-[10px] text-muted tracking-[0.16em]">№</div>
                <div className="font-black text-[24px] tracking-[-0.04em] text-ink">
                  {String(idx + 1).padStart(2, "0")}
                </div>
              </div>
              <div className="flex flex-col gap-2 flex-1 min-w-0">
                <div className="font-medium text-[18px] leading-[26px] text-ink tracking-[-0.005em]">
                  {task.statement}
                </div>
                <div className="flex items-baseline gap-[18px] flex-wrap">
                  <Pair k="Ответ">{task.answer}</Pair>
                  <Pair k="sympy" mono warn={warn}>
                    {task.expression ?? "-"}
                    {warn ? ` · ${issues[0]}` : ""}
                  </Pair>
                </div>
              </div>
              <div className="flex items-center gap-2 w-[140px] flex-shrink-0 justify-end pt-2">
                <div
                  className={`w-1.5 h-1.5 rounded-full ${
                    warn ? "bg-amber" : "bg-green"
                  }`}
                />
                <div
                  className={`text-[13px] font-semibold ${
                    warn ? "text-amber" : "text-green"
                  }`}
                >
                  {warn ? "На проверке" : "Сверено"}
                </div>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0 pt-1.5">
                <Link
                  href={`/task/${data.id}/${ws.variants[activeVariant].number}/${idx}`}
                  className="flex items-center justify-center w-8 h-8 rounded-md text-muted hover:text-ink hover:bg-hair transition-colors"
                  aria-label="Редактировать задачу"
                >
                  <Pencil size={14} strokeWidth={1.6} />
                </Link>
                <button
                  className="flex items-center justify-center w-8 h-8 rounded-md text-muted hover:text-ink hover:bg-hair transition-colors disabled:opacity-50"
                  aria-label="Перегенерировать задачу"
                  disabled={regen.isPending}
                  onClick={() =>
                    regen.mutate({
                      vn: ws.variants[activeVariant].number,
                      ti: idx,
                    })
                  }
                >
                  <RotateCw
                    size={14}
                    strokeWidth={1.6}
                    className={
                      regen.isPending &&
                      regen.variables?.vn === ws.variants[activeVariant].number &&
                      regen.variables?.ti === idx
                        ? "animate-spin"
                        : ""
                    }
                  />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatRow({
  value,
  desc,
  last = false,
}: {
  value: string;
  desc: string;
  last?: boolean;
}) {
  return (
    <div
      className={`flex items-baseline gap-4 ${
        last ? "" : "pb-3.5 border-b border-line"
      }`}
    >
      <div className="font-bold text-[22px] text-ink w-[100px]">{value}</div>
      <div className="text-[14px] font-medium text-ink-2 w-[240px]">{desc}</div>
    </div>
  );
}

function Pair({
  k,
  children,
  mono = false,
  warn = false,
}: {
  k: string;
  children: React.ReactNode;
  mono?: boolean;
  warn?: boolean;
}) {
  return (
    <div className="flex items-baseline gap-2">
      <div
        className={`mono text-[10px] tracking-[0.16em] uppercase ${
          warn ? "text-amber" : "text-muted"
        }`}
      >
        {k}
      </div>
      <div
        className={`${
          mono ? "mono text-[13px]" : "font-bold text-[15px]"
        } ${warn ? "text-amber" : "text-ink"}`}
      >
        {children}
      </div>
    </div>
  );
}
