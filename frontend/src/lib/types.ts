export type JobStatus =
  | "queued"
  | "cleaning"
  | "extracting"
  | "analyzing"
  | "indexing"
  | "ready"
  | "failed";

export type JobEvent = {
  step: JobStatus;
  message: string;
};

export type TablePayload = {
  columns: string[];
  rows: Record<string, string | number | null>[];
  markdown: string;
};

export type JobCreated = {
  id: string;
  filename: string;
  status: JobStatus;
};

export type JobSnapshot = {
  id: string;
  filename: string;
  chart_title: string;
  status: JobStatus;
  message: string;
  events: JobEvent[];
  indexed: boolean;
  index_error: string | null;
  error: string | null;
};

export type JobResult = {
  id: string;
  filename: string;
  chart_title: string;
  status: JobStatus;
  table: TablePayload | null;
  insight: string | null;
  indexed: boolean;
  index_error: string | null;
  error: string | null;
};

export type HealthResponse = {
  ok: boolean;
  ollama: boolean;
  database: boolean;
  model: string;
  message: string;
};

export type SourceDoc = {
  source?: string | null;
  title?: string | null;
  content?: string | null;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceDoc[];
  pending?: boolean;
};
