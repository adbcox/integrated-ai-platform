"""FastAPI router for RGC endpoints."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from roadmap_governance.database import get_db_dep
from roadmap_governance.models import IntegrityFinding, RoadmapItem
from roadmap_governance.schemas import (
    FindingLifecycleUpdate,
    IntegrityFindingResponse,
    RoadmapItemResponse,
)

router = APIRouter()


@router.get("/roadmap/items", response_model=List[RoadmapItemResponse])
def list_roadmap_items(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    db: Session = Depends(get_db_dep),
) -> List[RoadmapItemResponse]:
    q = db.query(RoadmapItem)
    if status is not None:
        q = q.filter(RoadmapItem.status == status)
    if category is not None:
        q = q.filter(RoadmapItem.category == category)
    rows = q.order_by(RoadmapItem.id).all()
    return [RoadmapItemResponse.model_validate(r) for r in rows]


@router.get("/integrity/findings", response_model=List[IntegrityFindingResponse])
def list_integrity_findings(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    finding_type: Optional[str] = Query(default=None, description="Filter by finding_type"),
    db: Session = Depends(get_db_dep),
) -> List[IntegrityFindingResponse]:
    q = db.query(IntegrityFinding)
    if status is not None:
        q = q.filter(IntegrityFinding.status == status)
    if finding_type is not None:
        q = q.filter(IntegrityFinding.finding_type == finding_type)
    rows = q.order_by(IntegrityFinding.detected_at.desc()).all()
    return [IntegrityFindingResponse.model_validate(r) for r in rows]


@router.get("/integrity/findings/{finding_id}", response_model=IntegrityFindingResponse)
def get_integrity_finding(
    finding_id: str,
    db: Session = Depends(get_db_dep),
) -> IntegrityFindingResponse:
    row = db.get(IntegrityFinding, finding_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    return IntegrityFindingResponse.model_validate(row)


@router.patch("/integrity/findings/{finding_id}", response_model=IntegrityFindingResponse)
def update_finding_lifecycle(
    finding_id: str,
    body: FindingLifecycleUpdate,
    db: Session = Depends(get_db_dep),
) -> IntegrityFindingResponse:
    row = db.get(IntegrityFinding, finding_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    row.status = body.status
    if body.resolution_note is not None:
        row.resolution_note = body.resolution_note
    db.commit()
    db.refresh(row)
    return IntegrityFindingResponse.model_validate(row)
