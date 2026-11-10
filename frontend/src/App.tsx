import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { Dropzone } from "./components/Dropzone";
import { StatusBanner } from "./components/StatusBanner";
import { Stepper } from "./components/Stepper";
import { Workspace } from "./components/Workspace";
import { askQuestion, createJob, fetchHealth, fetchJob, fetchResult, subscribeJobEvents } from "./lib/api";
import type { ChatMessage, HealthResponse, JobResult, JobStatus } from "./lib/types";

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus>("queued");
  const [message, setMessage] = useState("Menunggu giliran.");
  const [result, setResult] = useState<JobResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [asking, setAsking] = useState(false);

  const phase = useMemo(() => {
    if (result && (result.status === "ready" || (result.table && result.status !== "failed"))) return "workspace";
    if (file || jobId) return "process";
    return "atelier";
  }, [file, jobId, result]);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch(() =>
        setHealth({
          ok: false,
          ollama: false,
          database: false,
          model: "gemma4:12b",
          message: "API belum merespons. Jalankan uvicorn di port 8000.",
        }),
      );
  }, []);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  useEffect(() => {
    if (!jobId) return;
    const stop = subscribeJobEvents(jobId, async (payload) => {
      if (payload.message) setMessage(payload.message);
      if (payload.status) setStatus(payload.status as JobStatus);
      if (payload.type === "done" || payload.status === "ready" || payload.status === "failed") {
        try {
          const next = await fetchResult(jobId);
          setResult(next);
          if (next.error) setError(next.error);
        } catch (err) {
          setError(err instanceof Error ? err.message : "Gagal memuat hasil.");
        }
      }
    });
    return stop;
  }, [jobId]);

  useEffect(() => {
    if (!jobId || status === "ready" || status === "failed") return;
    const timer = window.setInterval(async () => {
      try {
        const snap = await fetchJob(jobId);
        setStatus(snap.status);
        setMessage(snap.message);
        if (snap.status === "ready" || snap.status === "failed") {
          const next = await fetchResult(jobId);
          setResult(next);
          if (next.error) setError(next.error);
        }
      } catch {
        /* SSE tetap menjadi saluran utama */
      }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [jobId, status]);

  async function handleFile(next: File) {
    if (preview) URL.revokeObjectURL(preview);
    setFile(next);
    setPreview(URL.createObjectURL(next));
    setResult(null);
    setMessages([]);
    setError(null);
    setStatus("queued");
    setMessage("Mengunggah grafik…");
    try {
      const created = await createJob(next);
      setJobId(created.id);
      setStatus(created.status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unggahan gagal.");
      setStatus("failed");
    }
  }

  function reset() {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null);
    setPreview(null);
    setJobId(null);
    setResult(null);
    setMessages([]);
    setError(null);
    setStatus("queued");
    setMessage("Menunggu giliran.");
  }

  async function sendQuestion(question: string) {
    const user: ChatMessage = { id: crypto.randomUUID(), role: "user", content: question };
    const assistantId = crypto.randomUUID();
    setMessages((prev) => [...prev, user, { id: assistantId, role: "assistant", content: "", pending: true }]);
    setAsking(true);
    try {
      await askQuestion(
        question,
        result?.filename ?? null,
        (delta) => {
          setMessages((prev) =>
            prev.map((item) =>
              item.id === assistantId
                ? { ...item, content: item.content + delta, pending: false }
                : item,
            ),
          );
        },
        (sources) => {
          setMessages((prev) =>
            prev.map((item) => (item.id === assistantId ? { ...item, sources } : item)),
          );
        },
      );
    } catch (err) {
      const text = err instanceof Error ? err.message : "Gagal menjawab.";
      setMessages((prev) =>
        prev.map((item) =>
          item.id === assistantId ? { ...item, content: text, pending: false } : item,
        ),
      );
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="paper-grain min-h-screen text-ink">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-8">
        <div>
          <p className="text-[11px] uppercase tracking-[0.22em] text-mute">Analisis Grafik</p>
          <p className="font-serif text-xl">Studio</p>
        </div>
        <p className="hidden text-sm text-mute sm:block">{health?.model ?? "Gemma lokal"} · privat di mesin Anda</p>
      </header>

      <main className="mx-auto max-w-6xl px-6 pb-20">
        <StatusBanner health={health} />

        <AnimatePresence mode="wait">
          {phase === "atelier" ? (
            <motion.section
              key="atelier"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.35 }}
            >
              <div className="mx-auto max-w-3xl pb-10 text-center">
                <p className="text-xs uppercase tracking-[0.22em] text-copper">Atelier finansial</p>
                <h1 className="mt-4 font-serif text-4xl leading-tight tracking-tight sm:text-5xl">
                  Unggah grafik.
                  <span className="block text-mute">Baca angkanya dengan tenang.</span>
                </h1>
                <p className="mx-auto mt-5 max-w-xl text-base leading-7 text-mute">
                  Satu ruang kerja: ekstraksi tabel, insight naratif, lalu tanya jawab yang hanya
                  merujuk data yang berhasil dibaca.
                </p>
              </div>
              <div className="mx-auto max-w-3xl">
                <Dropzone onFile={handleFile} />
              </div>
            </motion.section>
          ) : null}

          {phase === "process" ? (
            <motion.section
              key="process"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.35 }}
            >
              <div className="mb-10 max-w-2xl">
                <p className="text-xs uppercase tracking-[0.22em] text-copper">Sedang bekerja</p>
                <h1 className="mt-3 font-serif text-4xl">Membaca grafik Anda</h1>
                <p className="mt-3 text-mute">Proses ini bisa beberapa menit. Kami tidak mengirim data ke cloud.</p>
              </div>
              <Stepper
                status={status}
                message={message}
                previewUrl={preview}
                filename={file?.name ?? "grafik"}
              />
              {error ? (
                <div className="mt-8 rounded-2xl border border-copper/30 bg-cream px-5 py-4">
                  <p className="text-sm text-copper">{error}</p>
                  <button type="button" className="mt-3 text-sm underline" onClick={reset}>
                    Coba grafik lain
                  </button>
                </div>
              ) : null}
            </motion.section>
          ) : null}

          {phase === "workspace" && result ? (
            <motion.section
              key="workspace"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              <Workspace
                result={result}
                messages={messages}
                busy={asking}
                health={health}
                onSend={sendQuestion}
                onReset={reset}
              />
            </motion.section>
          ) : null}
        </AnimatePresence>
      </main>
    </div>
  );
}
