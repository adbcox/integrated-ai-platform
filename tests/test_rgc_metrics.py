"""Tests for RGC metrics capture and query service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from roadmap_governance.api_app import app
from roadmap_governance.database import get_db_dep
from roadmap_governance.metrics_service import capture_metrics, get_scope_metrics
from roadmap_governance.models import Base, CmdbEntity, IntegrityFinding, MetricSnapshot, RoadmapItem, RoadmapLink


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = factory()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    app.dependency_overrides[get_db_dep] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _seed_item(db, item_id: str, category: str = "platform", status: str = "planned") -> RoadmapItem:
    item = RoadmapItem(
        id=item_id,
        title=f"Item {item_id}",
        category=category,
        item_type="feature",
        priority="P1",
        status=status,
        description=None,
        source_path="docs/roadmap/ROADMAP_INDEX.md",
        source_hash="abc",
        naming_version="1.0",
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(item)
    db.flush()
    return item


def _seed_entity(db, canonical_name: str) -> CmdbEntity:
    entity = CmdbEntity(
        entity_id=str(uuid.uuid4()),
        entity_type="service",
        canonical_name=canonical_name,
        display_name=canonical_name,
        source_system="seed",
        entity_metadata={},
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(entity)
    db.flush()
    return entity


def _seed_link(db, roadmap_id: str, entity_id: str) -> RoadmapLink:
    link = RoadmapLink(
        roadmap_id=roadmap_id,
        entity_id=entity_id,
        link_type="exact_canonical",
        confidence=1.0,
        evidence_ref=None,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(link)
    db.flush()
    return link


def _seed_finding(db, item_id: str, status: str = "open") -> IntegrityFinding:
    f = IntegrityFinding(
        finding_id=str(uuid.uuid4()),
        finding_type="test_finding",
        severity="info",
        object_type="roadmap_item",
        object_ref=item_id,
        summary="test",
        details={},
        detected_at=_now(),
        status=status,
    )
    db.add(f)
    db.flush()
    return f


# ---------------------------------------------------------------------------
# Unit: capture_metrics
# ---------------------------------------------------------------------------

def test_empty_db_global_snapshot(db):
    result = capture_metrics(db)
    assert result.snapshots_written == 1  # global only (no categories)
    assert "global:global" in result.scopes_captured

    snap = get_scope_metrics(db, "global", "global")
    assert snap is not None
    assert snap.metrics["item_count"] == 0
    assert snap.metrics["package_count"] == 0


def test_global_item_count(db):
    _seed_item(db, "ITEM-001", category="platform")
    _seed_item(db, "ITEM-002", category="platform")
    capture_metrics(db)

    snap = get_scope_metrics(db, "global", "global")
    assert snap.metrics["item_count"] == 2


def test_per_category_snapshot_created(db):
    _seed_item(db, "ITEM-010", category="platform")
    _seed_item(db, "ITEM-011", category="security")
    result = capture_metrics(db)

    # global + platform + security = 3
    assert result.snapshots_written == 3
    assert "category:platform" in result.scopes_captured
    assert "category:security" in result.scopes_captured

    cat_snap = get_scope_metrics(db, "category", "platform")
    assert cat_snap is not None
    assert cat_snap.metrics["item_count"] == 1


def test_link_coverage_pct(db):
    item1 = _seed_item(db, "ITEM-020", category="platform")
    item2 = _seed_item(db, "ITEM-021", category="platform")
    entity = _seed_entity(db, "prod.rgc.api")
    _seed_link(db, item1.id, entity.entity_id)

    capture_metrics(db)

    snap = get_scope_metrics(db, "global", "global")
    assert snap.metrics["link_coverage_pct"] == 50.0


def test_open_finding_count(db):
    item = _seed_item(db, "ITEM-030")
    _seed_finding(db, item.id, status="open")
    _seed_finding(db, item.id, status="resolved")  # should not count

    capture_metrics(db)

    snap = get_scope_metrics(db, "global", "global")
    assert snap.metrics["open_finding_count"] == 1


def test_items_by_status_populated(db):
    _seed_item(db, "ITEM-040", status="planned")
    _seed_item(db, "ITEM-041", status="in_progress")
    capture_metrics(db)

    snap = get_scope_metrics(db, "global", "global")
    by_status = snap.metrics["items_by_status"]
    assert by_status["planned"] == 1
    assert by_status["in_progress"] == 1


def test_multiple_captures_returns_latest(db):
    _seed_item(db, "ITEM-050")
    capture_metrics(db)

    _seed_item(db, "ITEM-051")
    capture_metrics(db)

    snap = get_scope_metrics(db, "global", "global")
    assert snap.metrics["item_count"] == 2
    assert db.query(MetricSnapshot).count() == 4  # 2 runs × (global + platform)


def test_dry_run_does_not_persist(db):
    _seed_item(db, "ITEM-060")
    result = capture_metrics(db, dry_run=True)

    assert result.snapshots_written >= 1  # counted
    assert db.query(MetricSnapshot).count() == 0


# ---------------------------------------------------------------------------
# Unit: get_scope_metrics
# ---------------------------------------------------------------------------

def test_get_scope_metrics_none_for_missing(db):
    assert get_scope_metrics(db, "global", "global") is None


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

def test_api_metrics_capture(client, db):
    _seed_item(db, "ITEM-070", category="platform")
    resp = client.post("/metrics/capture")
    assert resp.status_code == 200
    body = resp.json()
    assert body["snapshots_written"] >= 2
    assert "global:global" in body["scopes_captured"]


def test_api_metrics_scope_404(client):
    resp = client.get("/metrics/scopes/global/global")
    assert resp.status_code == 404


def test_api_metrics_scope_returns_snapshot(client, db):
    _seed_item(db, "ITEM-080", category="platform")
    client.post("/metrics/capture")

    resp = client.get("/metrics/scopes/global/global")
    assert resp.status_code == 200
    body = resp.json()
    assert body["scope_type"] == "global"
    assert body["scope_ref"] == "global"
    assert body["metrics"]["item_count"] == 1


def test_api_metrics_category_scope(client, db):
    _seed_item(db, "ITEM-090", category="security")
    client.post("/metrics/capture")

    resp = client.get("/metrics/scopes/category/security")
    assert resp.status_code == 200
    assert resp.json()["metrics"]["item_count"] == 1


def test_api_metrics_capture_dry_run(client, db):
    _seed_item(db, "ITEM-100")
    resp = client.post("/metrics/capture?dry_run=true")
    assert resp.status_code == 200
    assert db.query(MetricSnapshot).count() == 0
