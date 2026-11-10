from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import pandas as pd

from src.api.schemas import JobEvent, JobStatus

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def dataframe_to_payload(df: pd.DataFrame) -> dict:
    clean = df.where(pd.notnull(df), None)
    columns = [str(c) for c in clean.columns]
    rows = []
    for _, row in clean.iterrows():
        item = {}
        for col in columns:
            val = row[col]
            if hasattr(val, "item"):
                try:
                    val = val.item()
                except Exception:
                    val = str(val)
            item[col] = val
        rows.append(item)
    try:
        markdown = df.to_markdown(index=False)
    except Exception:
        markdown = df.to_csv(index=False)
    return {"columns": columns, "rows": rows, "markdown": markdown}


@dataclass
class AnalysisJob:
    id: str
    filename: str
    chart_title: str
    original_path: Path
    cleaned_path: Path
    status: JobStatus = "queued"
    message: str = "Menunggu giliran."
    events: list[JobEvent] = field(default_factory=list)
    table: dict | None = None
    insight: str | None = None
    indexed: bool = False
    index_error: str | None = None
    error: str | None = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def emit(self, step: JobStatus, message: str) -> None:
        with self.lock:
            self.status = step
            self.message = message
            self.events.append(JobEvent(step=step, message=message))

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "id": self.id,
                "filename": self.filename,
                "chart_title": self.chart_title,
                "status": self.status,
                "message": self.message,
                "events": [e.model_dump() for e in self.events],
                "indexed": self.indexed,
                "index_error": self.index_error,
                "error": self.error,
            }

    def result(self) -> dict:
        with self.lock:
            return {
                "id": self.id,
                "filename": self.filename,
                "chart_title": self.chart_title,
                "status": self.status,
                "table": self.table,
                "insight": self.insight,
                "indexed": self.indexed,
                "index_error": self.index_error,
                "error": self.error,
            }


_jobs: dict[str, AnalysisJob] = {}
_jobs_lock = threading.Lock()


def get_job(job_id: str) -> AnalysisJob | None:
    with _jobs_lock:
        return _jobs.get(job_id)


def create_job(filename: str, content: bytes) -> AnalysisJob:
    job_id = uuid.uuid4().hex[:12]
    safe_name = Path(filename).name
    suffix = Path(safe_name).suffix.lower() or ".png"
    original_path = UPLOAD_DIR / f"{job_id}_original{suffix}"
    cleaned_path = UPLOAD_DIR / f"{job_id}_cleaned.png"
    original_path.write_bytes(content)
    title = Path(safe_name).stem.replace("_", " ").replace("-", " ").title()
    job = AnalysisJob(
        id=job_id,
        filename=safe_name,
        chart_title=title or "Diagram Finansial",
        original_path=original_path,
        cleaned_path=cleaned_path,
    )
    with _jobs_lock:
        _jobs[job_id] = job
    threading.Thread(target=run_pipeline, args=(job,), daemon=True).start()
    return job


def run_pipeline(job: AnalysisJob) -> None:
    try:
        from src.extraction.extractor import clean_image_with_opencv, extract_with_deplot
        from src.generation.analyze_vision import ask_gemma
        from src.generation.prompts import build_chart_analysis_prompt

        job.emit("cleaning", "Membersihkan garis dan label dari noise visual.")
        cleaned = clean_image_with_opencv(str(job.original_path))
        cv2.imwrite(str(job.cleaned_path), cleaned)

        job.emit("extracting", "Membaca angka dari garis dan sumbu grafik.")
        df = extract_with_deplot(cleaned)
        if df is None or df.empty:
            job.error = "Tabel gagal dibaca dari gambar. Coba grafik dengan label angka yang lebih jelas."
            job.emit("failed", job.error)
            return

        payload = dataframe_to_payload(df)
        with job.lock:
            job.table = payload

        job.emit("analyzing", "Menyusun pola, puncak, dan insight dari tabel.")
        prompt = build_chart_analysis_prompt(payload["markdown"])
        insight = ask_gemma(prompt)
        if insight.startswith("Error Ollama"):
            insight = (
                "Model lokal belum merespons. Tabel hasil ekstraksi tetap tersedia di workspace. "
                "Nyalakan Ollama (gemma4:12b) untuk menyusun insight naratif."
            )
        with job.lock:
            job.insight = insight

        job.emit("indexing", "Menyimpan potongan data ke basis vektor untuk tanya jawab.")
        try:
            from src.retrieval.indexer import index_to_vector_db, setup_database

            setup_database()
            index_to_vector_db(df, source_file=job.filename, chart_title=job.chart_title)
            with job.lock:
                job.indexed = True
        except Exception as exc:
            with job.lock:
                job.indexed = False
                job.index_error = str(exc)

        job.emit("ready", "Grafik siap dibaca. Ajukan pertanyaan di panel kanan.")
    except Exception as exc:
        job.error = str(exc)
        job.emit("failed", f"Pipeline terhenti: {exc}")


def job_events_payload(job: AnalysisJob) -> str:
    return json.dumps(job.snapshot(), ensure_ascii=False)
