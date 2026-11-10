import type { HealthResponse } from "../lib/types";

type Props = {
  health: HealthResponse | null;
};

export function StatusBanner({ health }: Props) {
  if (!health || (health.ollama && health.database)) return null;

  return (
    <div className="mx-auto mb-8 max-w-3xl rounded-2xl border border-copper/25 bg-cream/80 px-5 py-3 text-sm text-ink/80">
      <p className="font-medium text-copper">Beberapa layanan belum siap</p>
      <p className="mt-1 text-mute">{health.message}</p>
    </div>
  );
}
