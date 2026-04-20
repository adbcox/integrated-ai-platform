"""Tests for RGC Slice 4: roadmap-to-CMDB linking and impact view."""

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
from roadmap_governance.link_service import run_link_refresh, get_impact_view
from roadmap_governance.models import Base, CmdbEntity, RoadmapItem, RoadmapLink


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


def _seed_item(db, item_id: str, title: str, description: str = "") -> RoadmapItem:
    item = RoadmapItem(
        id=item_id,
        title=title,
        category="platform",
        item_type="feature",
        priority="P1",
        status="planned",
        description=description or None,
        source_path="docs/roadmap/ROADMAP_INDEX.md",
        source_hash="abc123",
        naming_version="1.0",
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(item)
    db.flush()
    return item


def _seed_entity(db, canonical_name: str, display_name: str = "", entity_type: str = "service") -> CmdbEntity:
    entity = CmdbEntity(
        entity_id=str(uuid.uuid4()),
        entity_type=entity_type,
        canonical_name=canonical_name,
        display_name=display_name or canonical_name,
        source_system="seed_file",
        entity_metadata={},
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(entity)
    db.flush()
    return entity


# ---------------------------------------------------------------------------
# Unit tests: run_link_refresh
# ---------------------------------------------------------------------------

def test_exact_match_creates_link(db):
    entity = _seed_entity(db, "prod.rgc.api")
    _seed_item(db, "ITEM-001", "Upgrade prod.rgc.api performance")

    result = run_link_refresh(db)

    assert result.items_processed == 1
    assert result.links_created == 1
    assert result.links_updated == 0
    assert result.findings_created == 0

    link = db.query(RoadmapLink).first()
    assert link is not None
    assert link.roadmap_id == "ITEM-001"
    assert link.entity_id == entity.entity_id
    assert link.link_type == "exact_canonical"
    assert link.confidence == 1.0
    assert link.evidence_ref == "canonical_name:prod.rgc.api"


def test_exact_match_in_description(db):
    _seed_entity(db, "prod.rgc.scheduler")
    _seed_item(db, "ITEM-002", "Platform work", description="Migrate prod.rgc.scheduler to k8s")

    result = run_link_refresh(db)

    assert result.links_created == 1
    assert result.findings_created == 0


def test_multiple_exact_matches_same_item(db):
    _seed_entity(db, "prod.rgc.api")
    _seed_entity(db, "prod.rgc.worker")
    _seed_item(db, "ITEM-003", "Refactor prod.rgc.api and prod.rgc.worker together")

    result = run_link_refresh(db)

    assert result.links_created == 2
    assert result.findings_created == 0


def test_unresolved_emits_finding(db):
    _seed_entity(db, "prod.rgc.api")
    _seed_item(db, "ITEM-004", "Improve database performance")

    result = run_link_refresh(db)

    assert result.links_created == 0
    assert result.findings_created == 1

    from roadmap_governance.models import IntegrityFinding
    f = db.query(IntegrityFinding).first()
    assert f.finding_type == "unresolved_cmdb_link"
    assert f.severity == "info"
    assert "ITEM-004" in f.object_ref


def test_ambiguous_emits_finding(db):
    # Two entities share last segment "api"
    _seed_entity(db, "prod.rgc.api")
    _seed_entity(db, "staging.rgc.api")
    # Item text contains "api" as a plain word but not a full canonical name
    _seed_item(db, "ITEM-005", "Work on the api layer improvements")

    result = run_link_refresh(db)

    assert result.links_created == 0
    assert result.findings_created == 1

    from roadmap_governance.models import IntegrityFinding
    f = db.query(IntegrityFinding).first()
    assert f.finding_type == "ambiguous_cmdb_link"
    assert f.severity == "warning"


def test_no_entities_all_unresolved(db):
    _seed_item(db, "ITEM-006", "Do something")
    _seed_item(db, "ITEM-007", "Do another thing")

    result = run_link_refresh(db)

    assert result.items_processed == 2
    assert result.links_created == 0
    assert result.findings_created == 2


def test_idempotent_rerun_does_not_duplicate(db):
    _seed_entity(db, "prod.rgc.api")
    _seed_item(db, "ITEM-008", "Upgrade prod.rgc.api")

    r1 = run_link_refresh(db)
    r2 = run_link_refresh(db)

    assert r1.links_created == 1
    assert r2.links_created == 0
    assert r2.links_unchanged == 1

    # Only one link in DB
    assert db.query(RoadmapLink).count() == 1


def test_idempotent_rerun_findings_not_duplicated(db):
    _seed_entity(db, "prod.rgc.api")
    _seed_item(db, "ITEM-009", "No match here")

    r1 = run_link_refresh(db)
    r2 = run_link_refresh(db)

    assert r1.findings_created == 1
    assert r2.findings_created == 0  # idempotent — already active


def test_dry_run_does_not_persist(db):
    _seed_entity(db, "prod.rgc.api")
    _seed_item(db, "ITEM-010", "Upgrade prod.rgc.api")

    result = run_link_refresh(db, dry_run=True)

    assert result.links_created == 1  # counted
    assert db.query(RoadmapLink).count() == 0  # not persisted


def test_dry_run_findings_not_persisted(db):
    _seed_entity(db, "prod.rgc.api")
    _seed_item(db, "ITEM-011", "No match")

    run_link_refresh(db, dry_run=True)

    from roadmap_governance.models import IntegrityFinding
    assert db.query(IntegrityFinding).count() == 0


# ---------------------------------------------------------------------------
# Unit tests: get_impact_view
# ---------------------------------------------------------------------------

def test_get_impact_view_none_for_missing(db):
    assert get_impact_view(db, "NONEXISTENT") is None


def test_get_impact_view_empty_links(db):
    _seed_item(db, "ITEM-020", "Orphan item")

    view = get_impact_view(db, "ITEM-020")

    assert view is not None
    assert view.roadmap_id == "ITEM-020"
    assert view.title == "Orphan item"
    assert view.links == []


def test_get_impact_view_returns_links(db):
    entity = _seed_entity(db, "prod.rgc.api", "RGC API")
    _seed_item(db, "ITEM-021", "Upgrade prod.rgc.api")
    run_link_refresh(db)

    view = get_impact_view(db, "ITEM-021")

    assert view is not None
    assert len(view.links) == 1
    lnk = view.links[0]
    assert lnk.entity_id == entity.entity_id
    assert lnk.canonical_name == "prod.rgc.api"
    assert lnk.display_name == "RGC API"
    assert lnk.link_type == "exact_canonical"
    assert lnk.confidence == 1.0


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

def test_api_impact_404_unknown(client):
    resp = client.get("/roadmap/items/NONEXISTENT/impact")
    assert resp.status_code == 404


def test_api_impact_empty_links(client, db):
    _seed_item(db, "ITEM-030", "Orphan item")

    resp = client.get("/roadmap/items/ITEM-030/impact")
    assert resp.status_code == 200
    body = resp.json()
    assert body["roadmap_id"] == "ITEM-030"
    assert body["links"] == []


def test_api_impact_returns_links(client, db):
    entity = _seed_entity(db, "prod.rgc.api", "RGC API")
    _seed_item(db, "ITEM-031", "Upgrade prod.rgc.api")
    run_link_refresh(db)

    resp = client.get("/roadmap/items/ITEM-031/impact")
    assert resp.status_code == 200
    body = resp.json()
    assert body["roadmap_id"] == "ITEM-031"
    assert len(body["links"]) == 1
    lnk = body["links"][0]
    assert lnk["entity_id"] == entity.entity_id
    assert lnk["canonical_name"] == "prod.rgc.api"
    assert lnk["link_type"] == "exact_canonical"
    assert lnk["confidence"] == 1.0


def test_api_links_list_all(client, db):
    _seed_entity(db, "prod.rgc.api")
    _seed_entity(db, "prod.rgc.worker")
    _seed_item(db, "ITEM-040", "Work on prod.rgc.api and prod.rgc.worker")
    run_link_refresh(db)

    resp = client.get("/roadmap/links")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2


def test_api_links_list_filtered(client, db):
    _seed_entity(db, "prod.rgc.api")
    _seed_entity(db, "prod.rgc.worker")
    _seed_item(db, "ITEM-041", "Work on prod.rgc.api only")
    _seed_item(db, "ITEM-042", "Work on prod.rgc.worker separately")
    run_link_refresh(db)

    resp = client.get("/roadmap/links?roadmap_id=ITEM-041")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["roadmap_id"] == "ITEM-041"


def test_api_links_list_empty(client):
    resp = client.get("/roadmap/links")
    assert resp.status_code == 200
    assert resp.json() == []


def test_exact_match_case_insensitive_item_text(db):
    """Item text is lowercased before matching; canonical_name must be lowercase."""
    _seed_entity(db, "prod.rgc.api")
    _seed_item(db, "ITEM-050", "UPGRADE PROD.RGC.API PERFORMANCE")

    result = run_link_refresh(db)
    assert result.links_created == 1


def test_segment_single_entity_no_link_and_unresolved(db):
    """Single entity whose last segment matches item text → no link, unresolved finding (not ambiguous)."""
    _seed_entity(db, "prod.rgc.api")
    _seed_item(db, "ITEM-060", "Work on the api component")

    result = run_link_refresh(db)

    assert result.links_created == 0
    # Single-segment match: segment_groups["api"] has only 1 entity → not ambiguous → unresolved
    assert result.findings_created == 1

    from roadmap_governance.models import IntegrityFinding
    f = db.query(IntegrityFinding).first()
    assert f.finding_type == "unresolved_cmdb_link"
