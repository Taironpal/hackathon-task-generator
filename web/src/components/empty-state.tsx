import { ArrowRight, Check, FileText, Layers, Wand2 } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

const QUICK_TOPICS: { topic: string; grade: number; subject: string }[] = [
  { topic: "проценты", grade: 5, subject: "математика" },
  { topic: "обыкновенные дроби", grade: 6, subject: "математика" },
  { topic: "скорость, время, расстояние", grade: 6, subject: "математика" },
  { topic: "линейное уравнение", grade: 7, subject: "математика" },
  { topic: "теорема Пифагора", grade: 8, subject: "математика" },
  { topic: "квадратное уравнение", grade: 8, subject: "математика" },
  { topic: "арифметическая прогрессия", grade: 9, subject: "математика" },
  { topic: "тригонометрия", grade: 9, subject: "математика" },
  { topic: "логарифмы", grade: 10, subject: "математика" },
  { topic: "производная", grade: 11, subject: "математика" },
];

export function EmptyState() {
  return (
    <div className="flex flex-col gap-10 sm:gap-14">
      {/* Hero + stats в одну плотную секцию */}
      <section className="grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-8 lg:gap-12 items-start">
        <div className="flex flex-col gap-4">
          <div className="eyebrow">сверка · математика 1-11 класс</div>
          <h1 className="font-black text-[34px] sm:text-[42px] lg:text-[52px] leading-[1.05] tracking-[-0.035em] text-ink">
            Тема, класс, количество.<br />
            Контрольная за&nbsp;полминуты.
          </h1>
          <p className="text-[15px] leading-[1.55] text-ink-2 max-w-[540px]">
            Учитель выбирает темы и&nbsp;класс. Сервис подбирает эталонные задачи
            из&nbsp;программы, размечает в&nbsp;них изменяемые параметры через
            GigaChat и&nbsp;генерирует N&nbsp;эквивалентных вариантов. Каждый
            ответ перепроверен sympy.
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Link href="/reference" className="btn-primary !text-[14px] !py-3.5 !px-5">
              Открыть конструктор
              <ArrowRight size={15} strokeWidth={1.8} />
            </Link>
            <Link
              href="/reference"
              className="btn-ghost !text-[13px]"
            >
              Посмотреть&nbsp;50+ тем
            </Link>
          </div>
        </div>

        {/* Stats компактно справа */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-5 lg:border-l lg:border-line lg:pl-10">
          <StatBlock value="1—11" suffix="класс">
            вся программа математики
          </StatBlock>
          <StatBlock value="50+" suffix="тем">
            из&nbsp;учебников и&nbsp;программы
          </StatBlock>
          <StatBlock value="100" suffix="%">
            ответов перепроверены sympy
          </StatBlock>
          <StatBlock value="2" suffix="DOCX">
            класс и&nbsp;ключи учителю
          </StatBlock>
        </div>
      </section>

      {/* Как работает + Темы — единая плотная двухколоночная секция */}
      <section className="grid grid-cols-1 lg:grid-cols-[1.2fr_1fr] gap-8 lg:gap-12 pt-7 border-t border-ink">
        <div className="flex flex-col gap-4">
          <header className="flex items-baseline justify-between gap-4">
            <div className="mono-caps ink">как это работает</div>
            <div className="mono-caps">3 шага · 1 окно</div>
          </header>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            <StepCard
              n="01"
              icon={<Layers size={14} strokeWidth={1.7} />}
              title="Соберите блоки"
            >
              Темы и&nbsp;классы. В&nbsp;одной контрольной можно смешать
              дроби&nbsp;6 + уравнения&nbsp;7.
            </StepCard>
            <StepCard
              n="02"
              icon={<Wand2 size={14} strokeWidth={1.7} />}
              title="LLM размечает"
            >
              GigaChat находит в&nbsp;эталоне изменяемые величины и&nbsp;формулу
              ответа.
            </StepCard>
            <StepCard
              n="03"
              icon={<FileText size={14} strokeWidth={1.7} />}
              title="Sympy проверяет"
            >
              Каждый ответ перепроверен. На&nbsp;выходе DOCX&nbsp;× 2:
              класс + учитель.
            </StepCard>
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <header className="flex items-baseline justify-between gap-4">
            <div className="mono-caps ink">популярные темы</div>
            <Link
              href="/reference"
              className="mono-caps hover:text-ink transition-colors"
            >
              все&nbsp;→
            </Link>
          </header>
          <div className="flex flex-wrap gap-1.5">
            {QUICK_TOPICS.map((q) => (
              <Link
                key={`${q.grade}-${q.topic}`}
                href={`/reference?topic=${encodeURIComponent(q.topic)}&grade=${q.grade}`}
                className="group flex items-baseline gap-1.5 text-[12px] font-medium text-ink-2 px-2.5 py-1.5 rounded-md border border-line hover:border-ink hover:bg-hair/50 transition-colors"
              >
                <span className="mono-caps group-hover:text-ink">
                  {q.grade}кл
                </span>
                <span className="group-hover:text-ink">{q.topic}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Под капотом — компактная плашка */}
      <section className="pt-6 border-t border-line flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-6">
        <div className="sm:w-32 flex-shrink-0 mono-caps ink">
          под капотом
        </div>
        <p className="text-[13px] leading-[1.6] text-ink-2 max-w-[760px]">
          <span className="font-semibold text-ink">GigaChat</span> размечает
          эталон со&nbsp;слотами.{" "}
          <span className="font-semibold text-ink">Sympy</span> считает
          ответ точной арифметикой — защита от&nbsp;галлюцинаций LLM.{" "}
          <span className="font-semibold text-ink">Python-docx</span>{" "}
          собирает два&nbsp;файла. <span className="font-semibold text-ink">Next.js</span>{" "}
          на&nbsp;фронте.
        </p>
        <div className="flex items-center gap-1.5 text-[11px] mono-caps flex-shrink-0">
          <Check size={11} strokeWidth={2.4} className="text-green" />
          кейс&nbsp;4 СберОбразования
        </div>
      </section>
    </div>
  );
}

function StatBlock({
  value,
  suffix,
  children,
}: {
  value: string;
  suffix: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline gap-1.5">
        <span className="font-black text-[30px] sm:text-[36px] text-ink tracking-[-0.04em] leading-none tabular-nums">
          {value}
        </span>
        <span className="mono-caps">{suffix}</span>
      </div>
      <div className="text-[11px] font-medium text-ink-2 leading-[1.35]">
        {children}
      </div>
    </div>
  );
}

function StepCard({
  n,
  icon,
  title,
  children,
}: {
  n: string;
  icon: ReactNode;
  title: string;
  children: ReactNode;
}) {
  return (
    <article className="rounded-lg border border-line p-3 sm:p-3.5 flex flex-col gap-1.5 bg-white">
      <div className="flex items-center justify-between">
        <div className="mono text-[10px] text-muted tracking-[0.16em] tabular-nums">
          {n}
        </div>
        <div className="w-6 h-6 rounded-md bg-hair flex items-center justify-center text-ink">
          {icon}
        </div>
      </div>
      <div className="font-bold text-[14px] tracking-[-0.015em] text-ink">
        {title}
      </div>
      <p className="text-[12px] leading-[1.5] text-ink-2">{children}</p>
    </article>
  );
}
