import type {
  AnalyzeRequest,
  AssignmentOut,
  ComposeRequest,
  GenerateVariantsRequest,
  GenerationRequest,
  LibraryOut,
  QuickGenerateRequest,
  ReferenceTask,
  Task,
  VariantSetOut,
  WorksheetOut,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  generate(body: GenerationRequest): Promise<WorksheetOut> {
    return req<WorksheetOut>("/generate", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getWorksheet(id: string): Promise<WorksheetOut> {
    return req<WorksheetOut>(`/worksheets/${id}`);
  },

  regenerateTask(
    id: string,
    variant_number: number,
    task_index: number,
    reason = "ручной запрос пользователя",
  ): Promise<WorksheetOut> {
    return req<WorksheetOut>(`/worksheets/${id}/regenerate_task`, {
      method: "POST",
      body: JSON.stringify({ variant_number, task_index, reason }),
    });
  },

  patchTask(
    id: string,
    variant_number: number,
    task_index: number,
    task: Task,
  ): Promise<WorksheetOut> {
    return req<WorksheetOut>(`/worksheets/${id}/task`, {
      method: "PUT",
      body: JSON.stringify({ variant_number, task_index, task }),
    });
  },

  downloadUrl(id: string, kind: "students" | "teacher"): string {
    return `${API_BASE}/worksheets/${id}/${kind}.docx`;
  },

  // ---------- Case 4 ----------

  analyze(body: AnalyzeRequest): Promise<ReferenceTask> {
    return req<ReferenceTask>("/analyze", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  generateVariants(body: GenerateVariantsRequest): Promise<VariantSetOut> {
    return req<VariantSetOut>("/generate-variants", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  getVariantSet(id: string): Promise<VariantSetOut> {
    return req<VariantSetOut>(`/variant-sets/${id}`);
  },

  variantSetDownloadUrl(id: string, kind: "students" | "teacher"): string {
    return `${API_BASE}/variant-sets/${id}/${kind}.docx`;
  },

  getLibrary(params: { query?: string; grade?: number; subject?: string; combined_only?: boolean } = {}): Promise<LibraryOut> {
    const qs = new URLSearchParams();
    if (params.query) qs.set("query", params.query);
    if (params.grade !== undefined) qs.set("grade", String(params.grade));
    if (params.subject) qs.set("subject", params.subject);
    if (params.combined_only) qs.set("combined_only", "true");
    const tail = qs.toString();
    return req<LibraryOut>(`/library${tail ? `?${tail}` : ""}`);
  },

  quickGenerate(body: QuickGenerateRequest): Promise<VariantSetOut> {
    return req<VariantSetOut>("/quick-generate", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  composeAssignment(body: ComposeRequest): Promise<AssignmentOut> {
    return req<AssignmentOut>("/compose-assignment", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  assignmentDownloadUrl(id: string, kind: "students" | "teacher"): string {
    return `${API_BASE}/assignments/${id}/${kind}.docx`;
  },
};
