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
  { topic: "плотность вещества", grade: 7, subject: "физика" },
  { topic: "сила тока", grade: 8, subject: "физика" },
];

export function EmptyState() {
  return (
    <div className="flex flex-col">
      {/* HERO - центрированный, во всю ширину */}
      <section className="flex flex-col items-center text-center gap-6 sm:gap-7 pt-10 sm:pt-16 lg:pt-24 pb-12 sm:pb-16">
        <div className="eyebrow">сверка · математика 1-11 класс</div>
        <h1 className="font-black text-[42px] sm:text-[64px] lg:text-[84px] leading-[1] tracking-[-0.045em] text-ink max-w-[1080px]">
          Тема, класс, количество.<br />
          Контрольная за&nbsp;полминуты.
        </h1>
        <p className="text-[16px] sm:text-[19px] leading-[1.5] text-ink-2 max-w-[680px]">
          Учитель выбирает темы и&nbsp;класс. Сервис подбирает эталонные задачи
          из&nbsp;программы, размечает изменяемые параметры через GigaChat
          и&nbsp;генерирует N&nbsp;эквивалентных вариантов. Каждый ответ
          перепроверен sympy.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
          <Link
            href="/reference"
            className="btn-primary !text-[15px] !py-4 !px-6"
          >
            Открыть конструктор
            <ArrowRight size={16} strokeWidth={1.8} />
          </Link>
          <Link
            href="/reference"
            className="btn-ghost !text-[14px] !py-3.5 !px-5"
          >
            Посмотреть&nbsp;50+ тем
          </Link>
        </div>
      </section>

      {/* STATS - 4 колонки во всю ширину */}
      <section className="border-y border-line py-10 sm:py-14 grid grid-cols-2 md:grid-cols-4 gap-y-10 gap-x-6">
        <StatBlock value="1-11" suffix="класс">
          вся программа математики
        </StatBlock>
        <StatBlock value="50+" suffix="тем">
          из&nbsp;12 учебников программы
        </StatBlock>
        <StatBlock value="100" suffix="%">
          ответов перепроверены sympy
        </StatBlock>
        <StatBlock value="2" suffix="DOCX">
          класс и&nbsp;ключи учителю
        </StatBlock>
      </section>

      {/* КАК РАБОТАЕТ - 3 широких карточки */}
      <section className="py-14 sm:py-20 flex flex-col gap-7">
        <header className="flex flex-col items-center text-center gap-2">
          <div className="eyebrow">как это работает</div>
          <h2 className="font-black text-[28px] sm:text-[36px] tracking-[-0.03em] text-ink">
            Три шага. Одно окно.
          </h2>
        </header>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StepCard
            n="01"
            icon={<Layers size={18} strokeWidth={1.5} />}
            title="Соберите блоки"
          >
            Темы и&nbsp;классы. В&nbsp;одной контрольной можно смешать
            несколько тем разных предметов&nbsp;- например, дроби&nbsp;6 + уравнения&nbsp;7
            + плотность&nbsp;8.
          </StepCard>
          <StepCard
            n="02"
            icon={<Wand2 size={18} strokeWidth={1.5} />}
            title="GigaChat размечает"
          >
            LLM находит в&nbsp;эталоне изменяемые величины, формулу ответа
            и&nbsp;разумные диапазоны. Учитель ничего не&nbsp;настраивает руками.
          </StepCard>
          <StepCard
            n="03"
            icon={<FileText size={18} strokeWidth={1.5} />}
            title="Sympy проверяет"
          >
            Подставляются значения, считаются ответы, бракуются некрасивые.
            На&nbsp;выходе DOCX&nbsp;× 2: для&nbsp;класса и&nbsp;ключи учителю.
          </StepCard>
        </div>
      </section>

      {/* ПОПУЛЯРНЫЕ ТЕМЫ - широкий чип-облако */}
      <section className="border-t border-line py-14 sm:py-20 flex flex-col items-center gap-7">
        <header className="flex flex-col items-center text-center gap-2">
          <div className="eyebrow">пример тем</div>
          <h2 className="font-black text-[28px] sm:text-[36px] tracking-[-0.03em] text-ink">
            От арифметики до&nbsp;производных.
          </h2>
          <p className="text-[14px] text-ink-2 max-w-[520px]">
            96 эталонов из&nbsp;Виленкин, Макарычев, Атанасян, Перышкин,
            Габриелян, Босова. Кликните, чтобы открыть в&nbsp;конструкторе.
          </p>
        </header>
        <div className="flex flex-wrap justify-center gap-2 max-w-[860px]">
          {QUICK_TOPICS.map((q) => (
            <Link
              key={`${q.grade}-${q.topic}`}
              href={`/reference?topic=${encodeURIComponent(q.topic)}&grade=${q.grade}&subject=${encodeURIComponent(q.subject)}`}
              className="group flex items-baseline gap-2 text-[13px] font-medium text-ink-2 px-3 py-2 rounded-md border border-line hover:border-ink hover:bg-hair/60 transition-colors"
            >
              <span className="mono-caps group-hover:text-ink">
                {q.grade}&nbsp;кл
              </span>
              <span className="group-hover:text-ink">{q.topic}</span>
            </Link>
          ))}
        </div>
        <Link
          href="/reference"
          className="mono-caps hover:text-ink transition-colors mt-2"
        >
          все&nbsp;тем в&nbsp;конструкторе&nbsp;→
        </Link>
      </section>

      {/* ПОД КАПОТОМ - компактная плашка с тёмным фоном */}
      <section className="border-t border-line py-14 sm:py-20 flex flex-col items-center text-center gap-5">
        <div className="eyebrow">под капотом</div>
        <p className="text-[15px] sm:text-[17px] leading-[1.6] text-ink-2 max-w-[760px]">
          <span className="font-bold text-ink">GigaChat</span>{" "}
          размечает эталон со&nbsp;слотами.{" "}
          <span className="font-bold text-ink">Sympy</span> подставляет
          значения и&nbsp;точной арифметикой считает ответ&nbsp;— защита
          от&nbsp;галлюцинаций LLM.{" "}
          <span className="font-bold text-ink">Python-docx</span>{" "}
          собирает два&nbsp;файла.{" "}
          <span className="font-bold text-ink">Next.js</span>{" "}
          на&nbsp;фронте.
        </p>
        <div className="flex items-center gap-1.5 text-[12px] mono-caps">
          <Check size={12} strokeWidth={2.4} className="text-green" />
          кейс&nbsp;4 хакатона СберОбразования
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
    <div className="flex flex-col items-center text-center gap-1.5">
      <div className="flex items-baseline gap-2">
        <span className="font-black text-[44px] sm:text-[56px] text-ink tracking-[-0.045em] leading-none tabular-nums">
          {value}
        </span>
        <span className="mono-caps">{suffix}</span>
      </div>
      <div className="text-[12px] font-medium text-ink-2 leading-[1.4]">
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
    <article className="rounded-xl border border-line p-5 sm:p-6 flex flex-col gap-3 bg-white">
      <div className="flex items-center justify-between">
        <div className="mono text-[11px] text-muted tracking-[0.16em] tabular-nums">
          {n}
        </div>
        <div className="w-9 h-9 rounded-lg bg-hair flex items-center justify-center text-ink">
          {icon}
        </div>
      </div>
      <div className="font-bold text-[18px] sm:text-[20px] tracking-[-0.02em] text-ink mt-1">
        {title}
      </div>
      <p className="text-[13px] sm:text-[14px] leading-[1.55] text-ink-2">
        {children}
      </p>
    </article>
  );
}
