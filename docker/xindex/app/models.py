"""Pydantic response models for the xindex API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Health(BaseModel):
    status: str
    last_ingest_at: str | None = None
    counts: dict[str, int] = Field(default_factory=dict)
    docs_root: str
    db_path: str


class RegisterRef(BaseModel):
    short_id: str
    category: str
    title: str
    summary: str


class ADRDetail(BaseModel):
    id: str
    short_id: str
    title: str
    status: str | None = None
    date: str | None = None
    phase: str | None = None
    source: str | None = None
    path: str
    body: str
    sections: dict[str, str] = Field(default_factory=dict)
    register_entry: RegisterRef | None = None


class RunbookDetail(BaseModel):
    name: str
    title: str
    path: str
    body: str


class SearchHit(BaseModel):
    kind: str
    ref: str
    title: str
    snippet: str
    rank: float


class SearchResponse(BaseModel):
    query: str
    type: str
    count: int
    results: list[SearchHit]


class RefreshAccepted(BaseModel):
    accepted: bool = True
    counts_before: dict[str, int]
    note: str = "Ingest scheduled in background. Poll /healthz for last_ingest_at."


class IngestSummary(BaseModel):
    adrs: int
    runbooks: int
    decision_register_entries: int
    last_ingest_at: str

    def as_meta(self) -> dict[str, Any]:
        return self.model_dump()
