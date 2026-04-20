"""Tests for RGC package planner (FeatureBlockPackage / FeatureBlockMember)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from roadmap_governance.api_app import app
from roadmap_governance.database import get_db_dep
from roadmap_governance.models import Base, CmdbEntity, FeatureBlockMember, FeatureBlockPackage, RoadmapItem, RoadmapLink
from roadmap_governance.planner_service import run_planner_refresh, _pkg_id, _score


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


def _seed_item(db, item_id: str, category: str = "platform", priority: str = "P1", status: str = "planned") -> RoadmapItem:
    item = RoadmapItem(
        id=item_id,
        title=f"Item {item_id}",
        category=category,
        item_type="feature",
        priority=priority,
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


# ---------------------------------------------------------------------------
# Unit: _pkg_id helper
# ---------------------------------------------------------------------------

def test_pkg_id_normalisation():
    assert _pkg_id("platform") == "PKG-PLATFORM"
    assert _pkg_id("security") == "PKG-SECURITY"


# ---------------------------------------------------------------------------
# Unit: scoring
# ---------------------------------------------------------------------------

def test_score_empty_items():
    assert _score([], set(), 0) == 0.0


def test_score_all_p1_no_links_no_findings(db):
    items = [_seed_item(db, f"ITEM-{i:03d}", priority="P1") for i in range(4)]
    # P1 weight=3, max=4*4=16, raw=12, normalised=0.75, no bonus, no penalty
    s = _score(items, set(), 0)
    assert abs(s - 0.75) < 1e-9


def test_score_link_bonus_applied(db):
    items = [_seed_item(db, "ITEM-B01", priority="P1")]
    linked = {items[0].id}
    s_with = _score(items, linked, 0)
    s_without = _score(items, set(), 0)
    assert s_with == s_without + 0.10


def test_score_finding_penalty(db):
    items = [_seed_item(db, "ITEM-C01", priority="P1")]
    s_clean = _score(items, set(), 0)
    s_penalised = _score(items, set(), 2)
    assert abs(s_clean - s_penalised - 0.10) < 1e-9


def test_score_clamped_to_one(db):
    items = [_seed_item(db, "ITEM-D01", priority="P0")]
    linked = {items[0].id}
    s = _score(items, linked, 0)
    assert s <= 1.0


def test_score_clamped_to_zero(db):
    items = [_seed_item(db, "ITEM-E01", priority="P3")]
    s = _score(items, set(), 100)
    assert s == 0.0


# ---------------------------------------------------------------------------
# Unit: run_planner_refresh
# ---------------------------------------------------------------------------

def test_creates_packages_per_category(db, tmp_path):
    _seed_item(db, "ITEM-001", category="platform")
    _seed_item(db, "ITEM-002", category="platform")
    _seed_item(db, "ITEM-003", category="security")

    result = run_planner_refresh(db, artifact_dir=tmp_path)

    assert result.packages_created == 2
    assert result.members_added == 3
    assert db.query(FeatureBlockPackage).count() == 2
    assert db.query(FeatureBlockMember).count() == 3


def test_package_ids_stable(db, tmp_path):
    _seed_item(db, "ITEM-010", category="platform")
    run_planner_refresh(db, artifact_dir=tmp_path)

    pkg = db.get(FeatureBlockPackage, "PKG-PLATFORM")
    assert pkg is not None
    assert pkg.scope == "platform"


def test_idempotent_rerun(db, tmp_path):
    _seed_item(db, "ITEM-020", category="platform")
    r1 = run_planner_refresh(db, artifact_dir=tmp_path)
    r2 = run_planner_refresh(db, artifact_dir=tmp_path)

    assert r1.packages_created == 1
    assert r2.packages_created == 0
    assert db.query(FeatureBlockPackage).count() == 1
    # Members are rebuilt each run
    assert db.query(FeatureBlockMember).count() == 1


def test_dry_run_does_not_persist(db, tmp_path):
    _seed_item(db, "ITEM-030", category="platform")
    result = run_planner_refresh(db, artifact_dir=tmp_path, dry_run=True)

    assert result.packages_created == 1  # counted
    assert db.query(FeatureBlockPackage).count() == 0  # not persisted
    assert db.query(FeatureBlockMember).count() == 0


def test_artifact_written(db, tmp_path):
    _seed_item(db, "ITEM-040", category="platform")
    run_planner_refresh(db, artifact_dir=tmp_path)

    artifact = tmp_path / "PKG-PLATFORM.json"
    assert artifact.exists()
    payload = json.loads(artifact.read_text())
    assert payload["package_id"] == "PKG-PLATFORM"
    assert len(payload["members"]) == 1


def test_link_bonus_increases_score(db, tmp_path):
    item = _seed_item(db, "ITEM-050", category="platform", priority="P1")
    entity = _seed_entity(db, "prod.rgc.api")
    _seed_link(db, item.id, entity.entity_id)

    run_planner_refresh(db, artifact_dir=tmp_path)

    pkg = db.get(FeatureBlockPackage, "PKG-PLATFORM")
    assert pkg.score > 0.75  # P1 normalised=0.75, +0.10 bonus


def test_no_items_no_packages(db, tmp_path):
    result = run_planner_refresh(db, artifact_dir=tmp_path)
    assert result.packages_created == 0
    assert db.query(FeatureBlockPackage).count() == 0


# ---------------------------------------------------------------------------
# API tests
# ---------------------------------------------------------------------------

def test_api_packages_refresh(client, db, tmp_path):
    _seed_item(db, "ITEM-060", category="platform")
    resp = client.post("/planner/packages/refresh")
    assert resp.status_code == 200
    body = resp.json()
    assert body["packages_created"] == 1


def test_api_packages_refresh_dry_run(client, db, tmp_path):
    _seed_item(db, "ITEM-061", category="platform")
    resp = client.post("/planner/packages/refresh?dry_run=true")
    assert resp.status_code == 200
    assert resp.json()["packages_created"] == 1
    assert db.query(FeatureBlockPackage).count() == 0


def test_api_list_packages(client, db, tmp_path):
    _seed_item(db, "ITEM-070", category="platform")
    _seed_item(db, "ITEM-071", category="security")
    client.post("/planner/packages/refresh")

    resp = client.get("/packages")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    scopes = {p["scope"] for p in body}
    assert scopes == {"platform", "security"}


def test_api_list_packages_filter(client, db):
    _seed_item(db, "ITEM-080", category="platform")
    _seed_item(db, "ITEM-081", category="security")
    client.post("/planner/packages/refresh")

    resp = client.get("/packages?scope=platform")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["scope"] == "platform"


def test_api_get_package(client, db):
    _seed_item(db, "ITEM-090", category="platform")
    client.post("/planner/packages/refresh")

    resp = client.get("/packages/PKG-PLATFORM")
    assert resp.status_code == 200
    body = resp.json()
    assert body["package_id"] == "PKG-PLATFORM"
    assert len(body["members"]) == 1


def test_api_get_package_404(client):
    resp = client.get("/packages/PKG-NONEXISTENT")
    assert resp.status_code == 404


def test_api_package_members_included(client, db):
    _seed_item(db, "ITEM-100", category="platform")
    _seed_item(db, "ITEM-101", category="platform")
    client.post("/planner/packages/refresh")

    resp = client.get("/packages/PKG-PLATFORM")
    members = resp.json()["members"]
    assert len(members) == 2
    assert all(m["member_role"] == "primary" for m in members)


def test_api_packages_sorted_by_score_desc(client, db):
    # P0 should outscore P3
    _seed_item(db, "ITEM-110", category="alpha", priority="P0")
    _seed_item(db, "ITEM-111", category="beta", priority="P3")
    client.post("/planner/packages/refresh")

    resp = client.get("/packages")
    packages = resp.json()
    assert packages[0]["score"] >= packages[1]["score"]
