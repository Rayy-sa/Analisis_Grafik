from typing import Any, Literal

from pydantic import BaseModel, Field

JobStatus = Literal[
    "queued",
    "cleaning",
    "extracting",
    "analyzing",
    "indexing",
    "ready",
    "failed",
]


class JobEvent(BaseModel):
    step: JobStatus
    message: str


class JobCreated(BaseModel):
    id: str
    filename: str
    status: JobStatus


class JobSnapshot(BaseModel):
    id: str
    filename: str
    chart_title: str
    status: JobStatus
    message: str
    events: list[JobEvent]
    indexed: bool
    index_error: str | None = None
    error: str | None = None


class TablePayload(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    markdown: str


class JobResult(BaseModel):
    id: str
    filename: str
    chart_title: str
    status: JobStatus
    table: TablePayload | None = None
    insight: str | None = None
    indexed: bool = False
    index_error: str | None = None
    error: str | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    source_file: str | None = None


class HealthResponse(BaseModel):
    ok: bool
    ollama: bool
    database: bool
    model: str
    message: str
