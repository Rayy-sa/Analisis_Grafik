import { useCallback, useId, useState } from "react";

type Props = {
  disabled?: boolean;
  onFile: (file: File) => void;
};

const ACCEPT = ["image/png", "image/jpeg", "image/webp"];

export function Dropzone({ disabled, onFile }: Props) {
  const inputId = useId();
  const [over, setOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const take = useCallback(
    (file?: File) => {
      if (!file) return;
      if (!ACCEPT.includes(file.type) && !/\.(png|jpe?g|webp)$/i.test(file.name)) {
        setError("Gunakan PNG, JPG, atau WEBP.");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setError("Ukuran maksimal 10 MB.");
        return;
      }
      setError(null);
      onFile(file);
    },
    [onFile],
  );

  return (
    <div>
      <label
        htmlFor={inputId}
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(event) => {
          event.preventDefault();
          setOver(false);
          if (!disabled) take(event.dataTransfer.files[0]);
        }}
        className={`group relative flex min-h-[280px] cursor-pointer flex-col items-center justify-center rounded-[28px] border border-dashed px-8 py-14 text-center transition ${
          over
            ? "border-copper bg-copper/8 shadow-sheet"
            : "border-line bg-cream/70 hover:border-copper/50 hover:bg-cream"
        } ${disabled ? "pointer-events-none opacity-60" : ""}`}
      >
        <input
          id={inputId}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          className="sr-only"
          disabled={disabled}
          onChange={(event) => take(event.target.files?.[0])}
        />
        <span className="mb-5 inline-flex h-14 w-14 items-center justify-center rounded-full border border-line bg-paper text-copper">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
            <path
              d="M12 16V4m0 0 4 4M12 4 8 8M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
        <p className="font-serif text-2xl tracking-tight text-ink">Letakkan grafik di sini</p>
        <p className="mt-3 max-w-md text-sm leading-relaxed text-mute">
          Atau klik untuk memilih berkas. Kami akan membersihkan gambar, mengekstrak tabel, lalu
          menulis insight dalam bahasa yang tenang.
        </p>
        <p className="mt-6 text-xs uppercase tracking-[0.18em] text-mute/80">PNG · JPG · WEBP · 10 MB</p>
      </label>
      {error ? <p className="mt-3 text-center text-sm text-copper">{error}</p> : null}
    </div>
  );
}
