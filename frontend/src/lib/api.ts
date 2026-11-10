import type { HealthResponse, JobCreated, JobResult, JobSnapshot, SourceDoc } from "./types";

async function readError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (Array.isArray(body?.detail)) {
      return body.detail.map((item: { msg?: string }) => item.msg ?? JSON.stringify(item)).join(" ");
    }
  } catch {
    /* ignore */
  }
  return `Permintaan gagal (${res.status}).`;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function createJob(file: File): Promise<JobCreated> {
  const data = new FormData();
  data.append("file", file);
  const res = await fetch("/api/jobs", { method: "POST", body: data });
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function fetchJob(id: string): Promise<JobSnapshot> {
  const res = await fetch(`/api/jobs/${id}`);
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export async function fetchResult(id: string): Promise<JobResult> {
  const res = await fetch(`/api/jobs/${id}/result`);
  if (!res.ok) throw new Error(await readError(res));
  return res.json();
}

export function subscribeJobEvents(
  id: string,
  onEvent: (payload: { type: string; step?: string; message?: string; status?: string }) => void,
): () => void {
  const source = new EventSource(`/api/jobs/${id}/events`);
  source.onmessage = (event) => {
    try {
      onEvent(JSON.parse(event.data));
    } catch {
      /* ignore malformed */
    }
  };
  source.onerror = () => {
    source.close();
  };
  return () => source.close();
}

export async function askQuestion(
  question: string,
  sourceFile: string | null,
  onDelta: (text: string) => void,
  onSources: (sources: SourceDoc[]) => void,
): Promise<void> {
  const res = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, source_file: sourceFile }),
  });
  if (!res.ok) throw new Error(await readError(res));
  if (!res.body) throw new Error("Aliran jawaban kosong.");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const line = chunk
        .split("\n")
        .filter((row) => row.startsWith("data:"))
        .map((row) => row.slice(5).trim())
        .join("");
      if (!line) continue;
      const payload = JSON.parse(line) as {
        type: string;
        delta?: string;
        sources?: SourceDoc[];
      };
      if (payload.sources) onSources(payload.sources);
      if (payload.delta) onDelta(payload.delta);
    }
  }
}

export function jobImageUrl(id: string, kind: "original" | "cleaned"): string {
  return `/api/jobs/${id}/image/${kind}`;
}
