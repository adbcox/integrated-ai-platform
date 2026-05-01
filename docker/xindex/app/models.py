"""Pydantic response models for the xindex API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PerSourceHealth(BaseModel):
    source: str
    last_ingest_at: str
    status: str            # 'ok' | 'error' | 'stale' | 'unknown'
    error: str = ""


class Health(BaseModel):
    status: str
    last_ingest_at: str | None = None
    counts: dict[str, int] = Field(default_factory=dict)
    docs_root: str
    db_path: str
    sources: list[PerSourceHealth] = Field(default_factory=list)


class RegisterRef(BaseModel):
    short_id: str
    category: str
    title: str
    summary: str


class PlaneIssueRef(BaseModel):
    external_id: str
    name: str
    state_name: str | None = None
    module_name: str | None = None
    updated_at: str | None = None


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
    plane_tracking: PlaneIssueRef | None = None


class RunbookDetail(BaseModel):
    name: str
    title: str
    path: str
    body: str


class ServiceDetail(BaseModel):
    name: str
    netbox_id: int | None = None
    protocol: str | None = None
    ports: list[int] = Field(default_factory=list)
    parent_kind: str | None = None
    parent_ref: str | None = None
    description: str = ""
    custom: dict[str, Any] = Field(default_factory=dict)
    source: str = "netbox"
    links: list["EntityLink"] = Field(default_factory=list)


class NodeDetail(BaseModel):
    name: str
    netbox_id: int | None = None
    role: str | None = None
    site: str | None = None
    status: str | None = None
    primary_ip: str | None = None
    description: str = ""
    custom: dict[str, Any] = Field(default_factory=dict)
    source: str = "netbox"
    links: list["EntityLink"] = Field(default_factory=list)


class EntityLink(BaseModel):
    from_kind: str
    from_ref: str
    to_kind: str
    to_ref: str
    link_type: str
    source: str


class LinksResponse(BaseModel):
    count: int
    results: list[EntityLink]


class PlaneIssueDetail(BaseModel):
    external_id: str
    plane_id: str
    name: str
    state_name: str | None = None
    module_name: str | None = None
    project_id: str | None = None
    description: str = ""
    updated_at: str | None = None
    source: str = "plane"
    links: list[EntityLink] = Field(default_factory=list)


class PlaneModuleDetail(BaseModel):
    name: str
    plane_id: str
    external_id: str | None = None
    description: str = ""
    source: str = "plane"
    issues: list[PlaneIssueRef] = Field(default_factory=list)


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
    services: int = 0
    nodes: int = 0
    entity_links: int = 0
    plane_issues: int = 0
    plane_modules: int = 0
    last_ingest_at: str

    def as_meta(self) -> dict[str, Any]:
        return self.model_dump()


# Resolve forward refs for self-referencing models.
ServiceDetail.model_rebuild()
NodeDetail.model_rebuild()
