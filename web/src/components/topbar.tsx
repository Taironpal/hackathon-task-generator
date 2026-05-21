import Link from "next/link";

interface Props {
  contextLabel?: string;
  saved?: { time: string; warn?: boolean } | null;
}

export function Topbar({ contextLabel = "новый документ", saved }: Props) {
  return (
    <div className="flex items-center justify-between gap-3 px-5 sm:px-10 lg:px-16 py-4 sm:py-6 lg:py-7 border-b border-line">
      <div className="flex items-baseline gap-2 sm:gap-3.5 min-w-0">
        <Link
          href="/"
          className="font-black text-[18px] sm:text-[22px] tracking-[-0.04em] text-ink flex-shrink-0"
        >
          Сверка
        </Link>
        <div className="mono-caps truncate hidden sm:block">{contextLabel}</div>
      </div>
      <div className="flex items-center gap-2 sm:gap-3 lg:gap-4 flex-shrink-0">
        {saved ? (
          <div
            className={`mono-caps ink flex items-center gap-1.5 ${
              saved.warn ? "!text-amber" : ""
            }`}
          >
            <div
              className={`w-[5px] h-[5px] rounded-full ${
                saved.warn ? "bg-amber" : "bg-green"
              }`}
            />
            <span className="hidden sm:inline">
              {saved.warn ? `не сохранено` : `сохранено · ${saved.time}`}
            </span>
          </div>
        ) : (
          <div className="mono-caps flex items-center gap-1.5">
            <div className="w-[5px] h-[5px] rounded-full bg-hint" />
            <span className="hidden sm:inline">черновик</span>
          </div>
        )}
        <div className="w-px h-3.5 bg-line hidden sm:block" />
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-ink text-white flex items-center justify-center font-bold text-[11px] sm:text-[12px] tracking-tight flex-shrink-0">
            МК
          </div>
          <div className="hidden md:flex flex-col leading-tight">
            <div className="text-[13px] font-semibold text-ink">
              Мария&nbsp;К.
            </div>
            <div className="mono-caps">Школа №&nbsp;57</div>
          </div>
        </div>
      </div>
    </div>
  );
}
