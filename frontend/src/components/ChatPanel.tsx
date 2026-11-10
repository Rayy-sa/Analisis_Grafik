import { useEffect, useRef, useState } from "react";
import type { ChatMessage, HealthResponse } from "../lib/types";

type Props = {
  messages: ChatMessage[];
  busy: boolean;
  indexed: boolean;
  indexError: string | null;
  health: HealthResponse | null;
  onSend: (question: string) => void;
};

const SUGGESTIONS = [
  "Apa tren utama dari grafik ini?",
  "Mana nilai tertinggi dan terendah?",
  "Ringkas insight untuk rapat direksi.",
];

export function ChatPanel({ messages, busy, indexed, indexError, health, onSend }: Props) {
  const [draft, setDraft] = useState("");
  const scroller = useRef<HTMLDivElement>(null);
  const askDisabled = busy || health?.ollama === false;

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  function submit(question: string) {
    const text = question.trim();
    if (!text || askDisabled) return;
    setDraft("");
    onSend(text);
  }

  return (
    <aside className="flex h-full min-h-[520px] flex-col rounded-[28px] border border-line bg-cream/90 shadow-sheet">
      <header className="border-b border-line px-5 py-4">
        <p className="text-xs uppercase tracking-[0.18em] text-mute">Tanya jawab</p>
        <h2 className="mt-1 font-serif text-2xl text-ink">Baca bersama data</h2>
        {!indexed ? (
          <p className="mt-2 text-xs leading-5 text-mute">
            {indexError
              ? "Basis vektor belum terhubung. Jawaban memakai pencarian jika database hidup."
              : "Data sedang disiapkan ke basis vektor."}
          </p>
        ) : (
          <p className="mt-2 text-xs text-forest">Terhubung ke potongan tabel grafik ini.</p>
        )}
      </header>

      <div ref={scroller} className="chat-scroll flex-1 space-y-4 overflow-y-auto px-5 py-4">
        {messages.length === 0 ? (
          <div className="space-y-2">
            {SUGGESTIONS.map((item) => (
              <button
                key={item}
                type="button"
                disabled={askDisabled}
                onClick={() => submit(item)}
                className="block w-full rounded-2xl border border-line bg-paper px-4 py-3 text-left text-sm text-ink transition hover:border-copper/40 disabled:opacity-50"
              >
                {item}
              </button>
            ))}
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className={message.role === "user" ? "ml-8" : "mr-4"}>
              <p className="mb-1 text-[11px] uppercase tracking-[0.16em] text-mute">
                {message.role === "user" ? "Anda" : "Analis"}
              </p>
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-6 ${
                  message.role === "user" ? "bg-ink text-cream" : "bg-paper text-ink"
                }`}
              >
                {message.content || (message.pending ? "Menyusun jawaban…" : "")}
              </div>
              {message.sources && message.sources.length > 0 ? (
                <ul className="mt-2 space-y-1">
                  {message.sources.map((source, index) => (
                    <li key={`${source.source}-${index}`} className="text-[11px] leading-5 text-mute">
                      {source.title || "Tabel"} · {source.source || "sumber"}
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ))
        )}
      </div>

      <form
        className="border-t border-line p-4"
        onSubmit={(event) => {
          event.preventDefault();
          submit(draft);
        }}
      >
        <label className="sr-only" htmlFor="ask">
          Pertanyaan
        </label>
        <div className="flex gap-2">
          <input
            id="ask"
            value={draft}
            disabled={askDisabled}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={health?.ollama === false ? "Nyalakan Ollama untuk bertanya" : "Tanyakan angka, tren, atau sumber…"}
            className="h-12 flex-1 rounded-full border border-line bg-paper px-4 text-sm outline-none ring-copper/30 focus:ring-2 disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={askDisabled || draft.trim().length < 3}
            className="h-12 rounded-full bg-copper px-5 text-sm text-cream transition hover:bg-copper/90 disabled:opacity-40"
          >
            Kirim
          </button>
        </div>
      </form>
    </aside>
  );
}
