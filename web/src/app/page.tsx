"use client";

import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { api } from "@/lib/api";
import { Topbar } from "@/components/topbar";
import { EmptyState } from "@/components/empty-state";
import { ResultsView } from "@/components/results-view";

function PageInner() {
  const sp = useSearchParams();
  const wsId = sp.get("ws");

  const { data, isLoading, error } = useQuery({
    queryKey: ["worksheet", wsId],
    queryFn: () => api.getWorksheet(wsId!),
    enabled: !!wsId,
  });

  const sheetLabel = data
    ? `контрольная № ${data.id.slice(0, 4).toUpperCase()}`
    : "сверка";
  const savedNow = new Date().toLocaleTimeString("ru", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <>
      <Topbar
        contextLabel={sheetLabel}
        saved={data ? { time: savedNow } : null}
      />
      <main className="flex-1 w-full">
        {!wsId && (
          <div className="px-5 sm:px-10 lg:px-16 max-w-[1200px] mx-auto w-full">
            <EmptyState />
          </div>
        )}
        {wsId && isLoading && (
          <div className="px-5 sm:px-10 lg:px-16 max-w-[1080px] mx-auto w-full mt-16 mono-caps">
            Загружаем контрольную…
          </div>
        )}
        {wsId && error && (
          <div className="px-5 sm:px-10 lg:px-16 max-w-[1080px] mx-auto w-full mt-16 text-amber">
            Не удалось загрузить: {(error as Error).message}
          </div>
        )}
        {data && (
          <div className="px-5 sm:px-10 lg:px-16 max-w-[1080px] mx-auto w-full">
            <ResultsView data={data} />
          </div>
        )}
      </main>
    </>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={null}>
      <PageInner />
    </Suspense>
  );
}
