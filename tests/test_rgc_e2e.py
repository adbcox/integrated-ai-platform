"""End-to-end RGC flow: sync → cmdb import → links refresh → integrity run → packages refresh → metrics capture → query."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from roadmap_governance.api_app import app
from roadmap_governance.cmdb_service import import_cmdb_entities
from roadmap_governance.database import get_db_dep
from roadmap_governance.integrity import run_integrity_review
from roadmap_governance.link_service import run_link_refresh
from roadmap_governance.metrics_service import capture_metrics, get_scope_metrics
from roadmap_governance.models import (
    Base,
    CmdbEntity,
    FeatureBlockPackage,
    IntegrityFinding,
    MetricSnapshot,
    RoadmapItem,
    RoadmapLink,
)
from roadmap_governance.planner_service import run_planner_refresh
from roadmap_governance.service import record_finding


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


def _seed_item_direct(db, item_id: str, title: str, category: str, priority: str) -> RoadmapItem:
    item = RoadmapItem(
        id=item_id,
        title=title,
        category=category,
        item_type="feature",
        priority=priority,
        status="planned",
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


# ---------------------------------------------------------------------------
# Full pipeline flow
# ---------------------------------------------------------------------------

def test_full_pipeline(db, tmp_path, client):
    """
    Step 1: Seed roadmap items (simulating sync output)
    Step 2: Import CMDB entities
    Step 3: Run links refresh
    Step 4: Run integrity review
    Step 5: Run packages refresh
    Step 6: Capture metrics
    Step 7: Query impact / findings / packages / metrics via API
    """

    # --- Step 1: seed roadmap items ---
    item1 = _seed_item_direct(db, "RM-PLATFORM-001", "Upgrade prod.rgc.api performance", "platform", "P1")
    item2 = _seed_item_direct(db, "RM-PLATFORM-002", "Extend prod.rgc.worker capacity", "platform", "P0")
    item3 = _seed_item_direct(db, "RM-SEC-001", "Harden auth layer", "security", "P2")
    db.commit()

    assert db.query(RoadmapItem).count() == 3

    # --- Step 2: import CMDB entities ---
    entities_data = [
        {"canonical_name": "prod.rgc.api", "display_name": "RGC API", "entity_type": "service"},
        {"canonical_name": "prod.rgc.worker", "display_name": "RGC Worker", "entity_type": "service"},
    ]
    cmdb_result = import_cmdb_entities(db, entities_data)
    assert cmdb_result.entities_created == 2

    # Verify via API
    resp = client.get("/cmdb/entities")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    # --- Step 3: run links refresh ---
    link_result = run_link_refresh(db)
    assert link_result.items_processed == 3
    assert link_result.links_created == 2  # item1 → api, item2 → worker
    assert link_result.findings_created == 1  # item3 unresolved (no cmdb match)

    # Verify impact views
    resp = client.get("/roadmap/items/RM-PLATFORM-001/impact")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["links"]) == 1
    assert body["links"][0]["canonical_name"] == "prod.rgc.api"

    resp = client.get("/roadmap/items/RM-SEC-001/impact")
    assert resp.json()["links"] == []

    # --- Step 4: run integrity review ---
    integrity_result = run_integrity_review(db, tmp_path)
    # All 3 items have valid IDs, priorities, categories, item_types
    # No near-duplicates → 0 findings from integrity check itself
    # (The unresolved_cmdb_link finding from step 3 is already persisted)
    assert integrity_result.items_checked == 3

    # Verify findings endpoint
    resp = client.get("/integrity/findings")
    assert resp.status_code == 200
    findings = resp.json()
    finding_types = {f["finding_type"] for f in findings}
    assert "unresolved_cmdb_link" in finding_types

    # --- Step 5: run packages refresh ---
    pkg_result = run_planner_refresh(db, artifact_dir=tmp_path / "packages")
    assert pkg_result.packages_created == 2  # platform + security
    assert pkg_result.members_added == 3

    # Verify artifacts written
    assert (tmp_path / "packages" / "PKG-PLATFORM.json").exists()
    assert (tmp_path / "packages" / "PKG-SECURITY.json").exists()

    # platform package score should include link bonus (items 1 and 2 are linked)
    pkg_platform = db.get(FeatureBlockPackage, "PKG-PLATFORM")
    assert pkg_platform is not None
    assert pkg_platform.score > 0.0

    # Verify packages API
    resp = client.get("/packages")
    assert resp.status_code == 200
    packages = resp.json()
    assert len(packages) == 2

    resp = client.get("/packages/PKG-PLATFORM")
    assert resp.status_code == 200
    assert len(resp.json()["members"]) == 2

    # --- Step 6: capture metrics ---
    metrics_result = capture_metrics(db)
    assert metrics_result.snapshots_written >= 3  # global + platform + security

    # --- Step 7: query metrics ---
    resp = client.get("/metrics/scopes/global/global")
    assert resp.status_code == 200
    global_metrics = resp.json()["metrics"]
    assert global_metrics["item_count"] == 3
    assert global_metrics["link_coverage_pct"] > 0.0
    assert global_metrics["package_count"] == 2

    resp = client.get("/metrics/scopes/category/platform")
    assert resp.status_code == 200
    cat_metrics = resp.json()["metrics"]
    assert cat_metrics["item_count"] == 2
    assert cat_metrics["link_coverage_pct"] == 100.0


def test_pipeline_idempotent_reruns(db, tmp_path):
    """Running all pipeline steps twice should not create duplicates."""
    _seed_item_direct(db, "RM-PLATFORM-001", "Upgrade prod.rgc.api performance", "platform", "P1")
    db.commit()

    entities_data = [{"canonical_name": "prod.rgc.api", "entity_type": "service", "display_name": "RGC API"}]

    for _ in range(2):
        import_cmdb_entities(db, entities_data)
        run_link_refresh(db)
        run_integrity_review(db, tmp_path)
        run_planner_refresh(db, artifact_dir=tmp_path / "packages")
        capture_metrics(db)

    assert db.query(CmdbEntity).count() == 1
    assert db.query(RoadmapLink).count() == 1
    assert db.query(FeatureBlockPackage).count() == 1
    # Findings: integrity produces findings for invalid category/item_type, links refresh
    # produces none (item has a link). Key assertion: count doesn't grow between runs
    # because record_finding is idempotent on active findings.
    count_after_both_runs = db.query(IntegrityFinding).count()
    # Verify idempotency: a third run must not add more findings
    import_cmdb_entities(db, entities_data)
    run_link_refresh(db)
    run_integrity_review(db, tmp_path)
    run_planner_refresh(db, artifact_dir=tmp_path / "packages")
    assert db.query(IntegrityFinding).count() == count_after_both_runs


def test_pipeline_api_links_endpoint(db, tmp_path, client):
    """GET /roadmap/links should list all persisted links."""
    _seed_item_direct(db, "RM-PLATFORM-001", "Upgrade prod.rgc.api performance", "platform", "P1")
    _seed_item_direct(db, "RM-PLATFORM-002", "Work on prod.rgc.worker", "platform", "P0")
    db.commit()

    import_cmdb_entities(db, [
        {"canonical_name": "prod.rgc.api", "entity_type": "service", "display_name": "API"},
        {"canonical_name": "prod.rgc.worker", "entity_type": "service", "display_name": "Worker"},
    ])
    run_link_refresh(db)

    resp = client.get("/roadmap/links")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
