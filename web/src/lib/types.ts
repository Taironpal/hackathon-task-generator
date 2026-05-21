/** Зеркало Pydantic-схем из backend/models.py + main.py */

export interface Task {
  statement: string;
  answer: string;
  expression: string | null;
  solution: string;
  grading_criteria: string;
  difficulty: number;
  topic: string;
}

export interface Variant {
  number: number;
  tasks: Task[];
}

export interface WorkSheet {
  subject: string;
  grade: number;
  topic: string;
  variants: Variant[];
  created_at: string;
}

export interface GenerationRequest {
  subject?: string;
  grade: number;
  topic: string;
  variants_count?: number;
  tasks_per_variant?: number;
  difficulty?: number;
  audience?: "standard" | "weak" | "strong";
  notes?: string | null;
}

export interface GenerationStats {
  total_tasks: number;
  first_pass_ok: number;
  regenerated: number;
  failed_after_regen: number;
  duplicates_replaced: number;
  elapsed_seconds: number;
  issues: string[];
  first_pass_rate: number;
}

export interface WorksheetOut {
  id: string;
  worksheet: WorkSheet;
  stats: GenerationStats;
  /** "{variant_number}_{task_index}" -> issues[] */
  task_issues: Record<string, string[]>;
}

// ---------- Case 4: эталон + слоты + варианты ----------

export type SlotType = "int" | "decimal" | "percent" | "fraction" | "string";

export interface Slot {
  name: string;
  original: unknown;
  type: SlotType;
  range: [number, number] | null;
  options: unknown[] | null;
  locked: boolean;
  description: string | null;
}

export interface ReferenceTask {
  raw_statement: string;
  template: string;
  slots: Slot[];
  answer_formula: string;
  original_answer: string | null;
  topic: string;
  subject: string;
  grade: number | null;
  difficulty_baseline: number;
}

export interface GeneratedVariant {
  number: number;
  statement: string;
  slot_values: Record<string, unknown>;
  answer: string;
  solution: string | null;
  difficulty: number;
  sympy_verified: boolean;
  issues: string[];
}

export interface VariantSet {
  id: string;
  reference: ReferenceTask;
  variants: GeneratedVariant[];
  created_at: string;
}

export interface VariantSetOut {
  id: string;
  variant_set: VariantSet;
}

export interface AnalyzeRequest {
  raw_statement: string;
  subject?: string;
  grade?: number | null;
}

export interface GenerateVariantsRequest {
  reference: ReferenceTask;
  count: number;
}

export interface QuickGenerateRequest {
  topic: string;
  grade: number;
  count: number;
}

// Конструктор контрольной из блоков

export interface BlockSpec {
  topic: string;
  grade: number;
  tasks_per_variant: number;
  subject: string;
}

export interface ComposeRequest {
  blocks: BlockSpec[];
  variants_count: number;
}

export interface CompositeBlock {
  topic: string;
  grade: number;
  tasks_per_variant: number;
  subject: string;
  reference: ReferenceTask;
  variant_tasks: GeneratedVariant[][];
}

export interface CompositeAssignment {
  id: string;
  blocks: CompositeBlock[];
  variants_count: number;
  created_at: string;
}

export interface AssignmentOut {
  id: string;
  assignment: CompositeAssignment;
}

// Библиотека эталонных задач

export interface LibraryItem {
  id: string;
  grade: number;
  subject: string;
  topic: string;
  subtopic: string;
  tags: string[];
  is_combined: boolean;
  statement: string;
  textbook?: string | null;
}

export interface LibraryOut {
  version: string;
  description: string;
  items: LibraryItem[];
}
