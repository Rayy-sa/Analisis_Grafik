import type { JobStatus } from "../lib/types";

const STEPS: { id: JobStatus; label: string; copy: string }[] = [
  { id: "cleaning", label: "Bersihkan", copy: "Menyaring noise, grid, dan warna garis." },
  { id: "extracting", label: "Ekstrak", copy: "Membaca angka dari garis dan sumbu." },
  { id: "analyzing", label: "Insight", copy: "Menyusun pola, puncak, dan kesimpulan." },
  { id: "indexing", label: "Siapkan tanya jawab", copy: "Menyimpan data agar bisa ditanya." },
];

const ORDER: JobStatus[] = ["queued", "cleaning", "extracting", "analyzing", "indexing", "ready", "failed"];

function rank(status: JobStatus): number {
  return ORDER.indexOf(status);
}

type Props = {
  status: JobStatus;
  message: string;
  previewUrl: string | null;
  filename: string;
};

export function Stepper({ status, message, previewUrl, filename }: Props) {
  const current = rank(status);

  return (
    <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[minmax(0,1fr)_280px]">
      <ol className="space-y-5">
        {STEPS.map((step, index) => {
          const stepRank = rank(step.id);
          const done = current > stepRank || status === "ready";
          const active = status === step.id || (status === "queued" && index === 0);
          return (
            <li key={step.id} className="flex gap-4">
              <span
                className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs ${
                  done
                    ? "bg-forest text-cream"
                    : active
                      ? "bg-copper text-cream"
                      : "border border-line bg-cream text-mute"
                }`}
              >
                {done ? "✓" : index + 1}
              </span>
              <div>
                <p className="font-medium text-ink">{step.label}</p>
                <p className="mt-1 text-sm text-mute">{active ? message || step.copy : step.copy}</p>
              </div>
            </li>
          );
        })}
      </ol>
      <aside className="overflow-hidden rounded-3xl border border-line bg-cream shadow-sheet">
        {previewUrl ? (
          <img src={previewUrl} alt={filename} className="h-56 w-full object-contain bg-paper" />
        ) : (
          <div className="flex h-56 items-center justify-center text-sm text-mute">Pratinjau grafik</div>
        )}
        <div className="border-t border-line px-4 py-3">
          <p className="truncate text-sm text-ink">{filename}</p>
          <p className="mt-1 text-xs uppercase tracking-[0.16em] text-mute">
            {status === "failed" ? "Terhenti" : status === "ready" ? "Siap dibaca" : "Sedang dibaca"}
          </p>
        </div>
      </aside>
    </div>
  );
}
