import { jobImageUrl } from "../lib/api";
import type { ChatMessage, HealthResponse, JobResult } from "../lib/types";
import { ChatPanel } from "./ChatPanel";
import { DataTable } from "./DataTable";
import { InsightCard } from "./InsightCard";
import { ReconstructedChart } from "./ReconstructedChart";

type Props = {
  result: JobResult;
  messages: ChatMessage[];
  busy: boolean;
  health: HealthResponse | null;
  onSend: (question: string) => void;
  onReset: () => void;
};

export function Workspace({ result, messages, busy, health, onSend, onReset }: Props) {
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
      <div className="space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-mute">Workspace</p>
            <h2 className="mt-1 font-serif text-3xl text-ink">{result.chart_title}</h2>
          </div>
          <button
            type="button"
            onClick={onReset}
            className="rounded-full border border-line px-4 py-2 text-sm text-ink hover:border-copper/50"
          >
            Analisis grafik lain
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <figure className="overflow-hidden rounded-3xl border border-line bg-cream">
            <img
              src={jobImageUrl(result.id, "original")}
              alt="Grafik asli"
              className="h-64 w-full object-contain bg-paper"
            />
            <figcaption className="border-t border-line px-4 py-2 text-xs uppercase tracking-[0.16em] text-mute">
              Asli
            </figcaption>
          </figure>
          <figure className="overflow-hidden rounded-3xl border border-line bg-cream">
            <img
              src={jobImageUrl(result.id, "cleaned")}
              alt="Grafik setelah dibersihkan"
              className="h-64 w-full object-contain bg-paper"
            />
            <figcaption className="border-t border-line px-4 py-2 text-xs uppercase tracking-[0.16em] text-mute">
              Setelah dibersihkan
            </figcaption>
          </figure>
        </div>

        {result.table ? (
          <section className="rounded-[28px] border border-line bg-cream p-5 shadow-sheet">
            <h3 className="font-serif text-xl text-ink">Rekonstruksi</h3>
            <p className="mb-4 mt-1 text-sm text-mute">Gambar ulang dari tabel yang berhasil dibaca.</p>
            <ReconstructedChart table={result.table} />
          </section>
        ) : null}

        {result.table ? (
          <section className="rounded-[28px] border border-line bg-cream p-5">
            <h3 className="mb-4 font-serif text-xl text-ink">Tabel ekstraksi</h3>
            <DataTable table={result.table} />
          </section>
        ) : null}

        <section className="rounded-[28px] border border-line bg-cream p-6">
          <h3 className="mb-4 font-serif text-xl text-ink">Insight</h3>
          <InsightCard insight={result.insight} />
        </section>
      </div>

      <ChatPanel
        messages={messages}
        busy={busy}
        indexed={result.indexed}
        indexError={result.index_error}
        health={health}
        onSend={onSend}
      />
    </div>
  );
}
