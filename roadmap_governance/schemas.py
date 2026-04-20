"""Pydantic response schemas for RGC API endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict


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
