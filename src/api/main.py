from __future__ import annotations

import asyncio
import json
import mimetypes
import os
import threading
from pathlib import Path

import urllib.request
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from src.api.jobs import (
    ALLOWED_SUFFIXES,
    ALLOWED_TYPES,
    MAX_UPLOAD_BYTES,
    create_job,
    get_job,
)
from src.api.schemas import AskRequest, HealthResponse, JobCreated
from src.generation.llm_client import MODEL_NAME, create_strict_prompt, generate_answer_stream

load_dotenv()

app = FastAPI(title="Studio Analisis Grafik", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ollama_ok() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2) as res:
            return res.status == 200
    except Exception:
        return False


def _database_ok() -> bool:
    try:
        import psycopg2

        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST", "127.0.0.1"),
            port=os.environ.get("DB_PORT", "5433"),
            database=os.environ.get("DB_NAME", "financial_rag"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASS", "postgres"),
            connect_timeout=2,
        )
        conn.close()
        return True
    except Exception:
        return False


@app.get("/api/health", response_model=HealthResponse)
def health():
    ollama = _ollama_ok()
    database = _database_ok()
    parts = []
    if not ollama:
        parts.append("Ollama belum merespons di port 11434.")
    if not database:
        parts.append("PostgreSQL/pgvector belum terhubung — tanya jawab akan dinonaktifkan.")
    message = " ".join(parts) if parts else "Semua layanan siap."
    return HealthResponse(
        ok=ollama,
        ollama=ollama,
        database=database,
        model=MODEL_NAME,
        message=message,
    )


@app.post("/api/jobs", response_model=JobCreated)
async def start_job(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    content_type = (file.content_type or "").lower()
    if suffix not in ALLOWED_SUFFIXES and content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unggah gambar PNG, JPG, atau WEBP.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Berkas kosong.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="Ukuran gambar maksimal 10 MB.")

    job = create_job(file.filename or "grafik.png", content)
    return JobCreated(id=job.id, filename=job.filename, status=job.status)


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan tidak ditemukan.")
    return job.snapshot()


@app.get("/api/jobs/{job_id}/result")
def job_result(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan tidak ditemukan.")
    return job.result()


@app.get("/api/jobs/{job_id}/events")
async def job_events(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan tidak ditemukan.")

    async def stream():
        sent = 0
        while True:
            snap = job.snapshot()
            events = snap["events"]
            while sent < len(events):
                event = events[sent]
                payload = json.dumps(
                    {"type": "event", **event, "status": event["step"]},
                    ensure_ascii=False,
                )
                yield f"data: {payload}\n\n"
                sent += 1
            if snap["status"] in {"ready", "failed"}:
                done = json.dumps({"type": "done", "status": snap["status"]}, ensure_ascii=False)
                yield f"data: {done}\n\n"
                break
            await asyncio.sleep(0.35)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/jobs/{job_id}/image/{kind}")
def job_image(job_id: str, kind: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pekerjaan tidak ditemukan.")
    path = job.original_path if kind == "original" else job.cleaned_path
    if kind not in {"original", "cleaned"}:
        raise HTTPException(status_code=404, detail="Jenis gambar tidak dikenal.")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Gambar belum tersedia.")
    media = mimetypes.guess_type(path.name)[0] or "image/png"
    return FileResponse(path, media_type=media)


@app.post("/api/ask")
async def ask(body: AskRequest):
    if not _ollama_ok():
        raise HTTPException(
            status_code=503,
            detail="Ollama tidak aktif. Nyalakan ollama serve lalu coba lagi.",
        )

    question = body.question.strip()

    try:
        from src.retrieval.search import execute_hybrid_search

        contexts = execute_hybrid_search(question, top_n_final=4)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Pencarian vektor gagal. Pastikan PostgreSQL berjalan. ({exc})",
        ) from exc

    if body.source_file:
        filtered = [doc for doc in contexts if doc.get("source") == body.source_file]
        if filtered:
            contexts = filtered

    if not contexts:
        async def empty():
            payload = {
                "type": "answer",
                "delta": "Data tidak tersedia di grafik/tabel yang saya baca.",
                "sources": [],
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'sources': []})}\n\n"

        return StreamingResponse(empty(), media_type="text/event-stream")

    prompt = create_strict_prompt(question, contexts)
    sources = [
        {"source": doc.get("source"), "title": doc.get("title"), "content": doc.get("content")}
        for doc in contexts
    ]

    async def stream_answer():
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def produce():
            try:
                for piece in generate_answer_stream(prompt):
                    asyncio.run_coroutine_threadsafe(queue.put(piece), loop)
            except Exception as exc:
                asyncio.run_coroutine_threadsafe(queue.put(f"\n\n(Gagal menghubungi model: {exc})"), loop)
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(None), loop)

        threading.Thread(target=produce, daemon=True).start()

        yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"
        while True:
            piece = await queue.get()
            if piece is None:
                break
            yield f"data: {json.dumps({'type': 'delta', 'delta': piece}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'sources': sources}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        stream_answer(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/")
def root():
    return {"service": "studio-analisis-grafik", "docs": "/docs"}
