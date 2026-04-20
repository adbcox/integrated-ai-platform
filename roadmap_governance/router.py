"""FastAPI router for RGC endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from roadmap_governance.database import get_db_dep
from roadmap_governance.integrity import run_integrity_review
from roadmap_governance.link_service import get_impact_view
from roadmap_governance.metrics_service import capture_metrics, get_scope_metrics
from roadmap_governance.models import (
    CmdbEntity,
    FeatureBlockMember,
    FeatureBlockPackage,
    IntegrityFinding,
    RoadmapItem,
    RoadmapLink,
)
from roadmap_governance.planner_service import run_planner_refresh
from roadmap_governance.service import sync_roadmap
from roadmap_governance.schemas import (
    CmdbEntityResponse,
    FeatureBlockMemberResponse,
    FeatureBlockPackageResponse,
    FindingLifecycleUpdate,
    IntegrityFindingResponse,
    MetricSnapshotResponse,
    RoadmapImpactResponse,
    RoadmapItemResponse,
    RoadmapLinkResponse,
)

router = APIRouter()

_REPO_ROOT = Path(__file__).resolve().parent.parent


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/sync/roadmap", response_model=dict)
def trigger_sync(
    dry_run: bool = Query(default=False),
    db: Session = Depends(get_db_dep),
) -> dict:
    result = sync_roadmap(db, _REPO_ROOT, dry_run=dry_run)
    return {
        "items_created": result.items_created,
        "items_updated": result.items_updated,
        "items_unchanged": result.items_unchanged,
        "findings_created": result.findings_created,
        "artifact_path": result.artifact_path,
    }


@router.post("/reviews/integrity", response_model=dict)
def trigger_integrity_review(
    dry_run: bool = Query(default=False),
    db: Session = Depends(get_db_dep),
) -> dict:
    result = run_integrity_review(db, _REPO_ROOT, dry_run=dry_run)
    return {
        "items_checked": result.items_checked,
        "findings_created": result.findings_created,
        "findings_skipped": result.findings_skipped,
        "artifact_path": str(result.artifact_path) if result.artifact_path else None,
    }


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


@router.get("/cmdb/entities", response_model=List[CmdbEntityResponse])
def list_cmdb_entities(
    entity_type: Optional[str] = Query(default=None, description="Filter by entity_type"),
    environment: Optional[str] = Query(default=None, description="Filter by environment"),
    db: Session = Depends(get_db_dep),
) -> List[CmdbEntityResponse]:
    q = db.query(CmdbEntity)
    if entity_type is not None:
        q = q.filter(CmdbEntity.entity_type == entity_type)
    if environment is not None:
        q = q.filter(CmdbEntity.environment == environment)
    rows = q.order_by(CmdbEntity.canonical_name).all()
    return [CmdbEntityResponse.model_validate(r) for r in rows]


@router.get("/cmdb/entities/{entity_id}", response_model=CmdbEntityResponse)
def get_cmdb_entity(
    entity_id: str,
    db: Session = Depends(get_db_dep),
) -> CmdbEntityResponse:
    row = db.get(CmdbEntity, entity_id)
    if row is None:
        raise HTTPException(status_code=404, detail="CMDB entity not found")
    return CmdbEntityResponse.model_validate(row)


@router.get("/roadmap/items/{item_id}", response_model=RoadmapItemResponse)
def get_roadmap_item(
    item_id: str,
    db: Session = Depends(get_db_dep),
) -> RoadmapItemResponse:
    row = db.get(RoadmapItem, item_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Roadmap item not found")
    return RoadmapItemResponse.model_validate(row)


@router.get("/roadmap/items/{item_id}/impact", response_model=RoadmapImpactResponse)
def get_roadmap_item_impact(
    item_id: str,
    db: Session = Depends(get_db_dep),
) -> RoadmapImpactResponse:
    result = get_impact_view(db, item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Roadmap item not found")
    return result


@router.get("/roadmap/links", response_model=List[RoadmapLinkResponse])
def list_roadmap_links(
    roadmap_id: Optional[str] = Query(default=None, description="Filter by roadmap_id"),
    db: Session = Depends(get_db_dep),
) -> List[RoadmapLinkResponse]:
    q = db.query(RoadmapLink)
    if roadmap_id is not None:
        q = q.filter(RoadmapLink.roadmap_id == roadmap_id)
    rows = q.order_by(RoadmapLink.roadmap_id, RoadmapLink.entity_id).all()
    return [RoadmapLinkResponse.model_validate(r) for r in rows]


# ---------------------------------------------------------------------------
# Package planner
# ---------------------------------------------------------------------------

@router.post("/planner/packages/refresh", response_model=dict)
def refresh_packages(
    dry_run: bool = Query(default=False, description="Evaluate without persisting"),
    db: Session = Depends(get_db_dep),
) -> dict:
    result = run_planner_refresh(db, dry_run=dry_run)
    return {
        "packages_created": result.packages_created,
        "packages_updated": result.packages_updated,
        "packages_unchanged": result.packages_unchanged,
        "members_added": result.members_added,
        "artifact_paths": result.artifact_paths,
    }


@router.get("/packages", response_model=List[FeatureBlockPackageResponse])
def list_packages(
    scope: Optional[str] = Query(default=None, description="Filter by scope (category)"),
    db: Session = Depends(get_db_dep),
) -> List[FeatureBlockPackageResponse]:
    q = db.query(FeatureBlockPackage)
    if scope is not None:
        q = q.filter(FeatureBlockPackage.scope == scope)
    packages = q.order_by(FeatureBlockPackage.score.desc()).all()
    out = []
    for pkg in packages:
        members = (
            db.query(FeatureBlockMember)
            .filter(FeatureBlockMember.package_id == pkg.package_id)
            .all()
        )
        resp = FeatureBlockPackageResponse.model_validate(pkg)
        resp.members = [FeatureBlockMemberResponse.model_validate(m) for m in members]
        out.append(resp)
    return out


@router.get("/packages/{package_id}", response_model=FeatureBlockPackageResponse)
def get_package(
    package_id: str,
    db: Session = Depends(get_db_dep),
) -> FeatureBlockPackageResponse:
    pkg = db.get(FeatureBlockPackage, package_id)
    if pkg is None:
        raise HTTPException(status_code=404, detail="Package not found")
    members = (
        db.query(FeatureBlockMember)
        .filter(FeatureBlockMember.package_id == package_id)
        .all()
    )
    resp = FeatureBlockPackageResponse.model_validate(pkg)
    resp.members = [FeatureBlockMemberResponse.model_validate(m) for m in members]
    return resp


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

@router.post("/metrics/capture", response_model=dict)
def capture_metrics_endpoint(
    dry_run: bool = Query(default=False),
    db: Session = Depends(get_db_dep),
) -> dict:
    result = capture_metrics(db, dry_run=dry_run)
    return {
        "snapshots_written": result.snapshots_written,
        "scopes_captured": result.scopes_captured,
    }


@router.get("/metrics/scopes/{scope_type}/{scope_ref:path}", response_model=MetricSnapshotResponse)
def get_metrics_for_scope(
    scope_type: str,
    scope_ref: str,
    db: Session = Depends(get_db_dep),
) -> MetricSnapshotResponse:
    snap = get_scope_metrics(db, scope_type, scope_ref)
    if snap is None:
        raise HTTPException(status_code=404, detail="No metrics found for this scope")
    return MetricSnapshotResponse.model_validate(snap)
