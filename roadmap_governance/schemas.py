"""Pydantic response schemas for RGC API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class RoadmapItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    category: str
    item_type: str
    priority: str
    status: str
    description: Optional[str]
    source_path: str
    source_hash: str
    naming_version: str
    created_at: datetime
    updated_at: datetime


class IntegrityFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    finding_id: str
    finding_type: str
    severity: str
    object_type: str
    object_ref: str
    summary: str
    details: Any
    detected_at: datetime
    status: str
    resolution_note: Optional[str]


class FindingLifecycleUpdate(BaseModel):
    status: Literal["resolved", "accepted", "suppressed"]
    resolution_note: Optional[str] = None


class CmdbEntityResponse(BaseModel):
    # populate_by_name=True lets tests construct the model using the Python field name.
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    entity_id: str
    entity_type: str
    canonical_name: str
    display_name: str
    platform: Optional[str]
    environment: Optional[str]
    criticality: Optional[str]
    owner: Optional[str]
    lifecycle_state: Optional[str]
    source_system: Optional[str]
    external_ref: Optional[str]
    # ORM attribute is entity_metadata (avoids shadowing Base.metadata); JSON key is metadata.
    metadata: Any = Field(default={}, validation_alias="entity_metadata")
    created_at: datetime
    updated_at: datetime


class RoadmapLinkItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity_id: str
    link_type: str
    confidence: float
    evidence_ref: Optional[str]
    canonical_name: str
    display_name: str
    entity_type: str
    created_at: datetime
    updated_at: datetime


class RoadmapImpactResponse(BaseModel):
    roadmap_id: str
    title: str
    links: List[RoadmapLinkItem]


class RoadmapLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    roadmap_id: str
    entity_id: str
    link_type: str
    confidence: float
    evidence_ref: Optional[str]
    created_at: datetime
    updated_at: datetime
