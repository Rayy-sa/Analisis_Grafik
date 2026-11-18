import { useEffect, useMemo, useState } from "react";
import type { HealthResponse } from "../lib/types";

type Props = {
  health: HealthResponse | null;
};

export function StatusBanner({ health }: Props) {
  const [hidden, setHidden] = useState(false);

  const lines = useMemo(() => {
    if (!health) return [];
    const items: string[] = [];
    if (!health.ollama) items.push("Ollama belum terhubung.");
    if (!health.database) items.push("PostgreSQL belum terhubung.");
    return items;
  }, [health]);

  useEffect(() => {
    setHidden(false);
  }, [health?.ollama, health?.database]);

  if (hidden || lines.length === 0) return null;

  return (
    <div
      role="status"
      className="fixed bottom-6 right-6 z-50 max-w-sm rounded-2xl border border-line bg-cream px-4 py-3 shadow-sheet"
    >
      <div className="flex items-start gap-3">
        <div className="min-w-0 flex-1 text-sm leading-6 text-ink">
          {lines.map((line) => (
            <p key={line}>{line}</p>
          ))}
        </div>
        <button
          type="button"
          onClick={() => setHidden(true)}
          className="shrink-0 rounded-full px-1.5 text-sm text-mute hover:text-ink"
          aria-label="Tutup notifikasi"
        >
          ×
        </button>
      </div>
    </div>
  );
}
