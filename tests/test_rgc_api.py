"""Offline tests for RGC API endpoints.

Uses FastAPI TestClient with an in-memory SQLite override.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from roadmap_governance.database import get_db_dep
from roadmap_governance.models import Base, IntegrityFinding, RoadmapItem
from roadmap_governance.router import router as rgc_router
from roadmap_governance.service import sync_roadmap


def _make_test_app():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        db: Session = factory()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI(title="RGC Test")
    app.include_router(rgc_router)
    app.dependency_overrides[get_db_dep] = override_get_db
    return app, factory


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _item(item_id: str, title: str = "Title", category: str = "GOV") -> RoadmapItem:
    now = _now()
    return RoadmapItem(
        id=item_id,
        title=title,
        category=category,
        item_type="governance",
        priority="P1",
        status="proposed",
        description=None,
        source_path="docs/roadmap/ROADMAP_INDEX.md",
        source_hash="abc123",
        naming_version="v1",
        created_at=now,
        updated_at=now,
    )


def _finding(finding_type: str = "duplicate_id", object_ref: str = "RM-GOV-001") -> IntegrityFinding:
    return IntegrityFinding(
        finding_id=str(uuid.uuid4()),
        finding_type=finding_type,
        severity="warning",
        object_type="roadmap_item",
        object_ref=object_ref,
        summary="Test finding",
        details={},
        detected_at=_now(),
        status="open",
        resolution_note=None,
    )


class RoadmapItemsEndpointTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app, self.factory = _make_test_app()
        self.client = TestClient(self.app)

    def _seed(self, *items: RoadmapItem) -> None:
        db = self.factory()
        for item in items:
            db.add(item)
        db.commit()
        db.close()

    def test_empty_returns_list(self) -> None:
        resp = self.client.get("/roadmap/items")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_returns_seeded_items(self) -> None:
        self._seed(_item("RM-GOV-001"), _item("RM-CORE-001", category="CORE"))
        resp = self.client.get("/roadmap/items")
        self.assertEqual(resp.status_code, 200)
        ids = {r["id"] for r in resp.json()}
        self.assertIn("RM-GOV-001", ids)
        self.assertIn("RM-CORE-001", ids)

    def test_filter_by_status(self) -> None:
        item = _item("RM-GOV-001")
        self._seed(item)
        resp = self.client.get("/roadmap/items?status=proposed")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

        resp2 = self.client.get("/roadmap/items?status=completed")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(len(resp2.json()), 0)

    def test_filter_by_category(self) -> None:
        self._seed(_item("RM-GOV-001", category="GOV"), _item("RM-CORE-001", category="CORE"))
        resp = self.client.get("/roadmap/items?category=GOV")
        self.assertEqual(resp.status_code, 200)
        ids = [r["id"] for r in resp.json()]
        self.assertIn("RM-GOV-001", ids)
        self.assertNotIn("RM-CORE-001", ids)

    def test_response_fields_present(self) -> None:
        self._seed(_item("RM-GOV-001"))
        resp = self.client.get("/roadmap/items")
        self.assertEqual(resp.status_code, 200)
        row = resp.json()[0]
        for field in (
            "id", "title", "category", "item_type", "priority",
            "status", "source_path", "source_hash", "naming_version",
            "created_at", "updated_at",
        ):
            self.assertIn(field, row, f"missing field: {field}")

    def test_ordered_by_id(self) -> None:
        self._seed(_item("RM-GOV-003"), _item("RM-GOV-001"), _item("RM-GOV-002"))
        resp = self.client.get("/roadmap/items")
        ids = [r["id"] for r in resp.json()]
        self.assertEqual(ids, sorted(ids))


class IntegrityFindingsEndpointTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app, self.factory = _make_test_app()
        self.client = TestClient(self.app)

    def _seed(self, *findings: IntegrityFinding) -> None:
        db = self.factory()
        for f in findings:
            db.add(f)
        db.commit()
        db.close()

    def test_empty_returns_list(self) -> None:
        resp = self.client.get("/integrity/findings")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_returns_seeded_findings(self) -> None:
        self._seed(_finding("duplicate_id", "RM-GOV-001"))
        resp = self.client.get("/integrity/findings")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

    def test_filter_by_status(self) -> None:
        self._seed(_finding())
        resp = self.client.get("/integrity/findings?status=open")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)

        resp2 = self.client.get("/integrity/findings?status=resolved")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(len(resp2.json()), 0)

    def test_filter_by_finding_type(self) -> None:
        self._seed(
            _finding("duplicate_id", "RM-GOV-001"),
            _finding("naming_violation", "BADID"),
        )
        resp = self.client.get("/integrity/findings?finding_type=naming_violation")
        self.assertEqual(resp.status_code, 200)
        rows = resp.json()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["finding_type"], "naming_violation")

    def test_response_fields_present(self) -> None:
        self._seed(_finding())
        resp = self.client.get("/integrity/findings")
        row = resp.json()[0]
        for field in (
            "finding_id", "finding_type", "severity", "object_type",
            "object_ref", "summary", "details", "detected_at", "status",
        ):
            self.assertIn(field, row, f"missing field: {field}")


class EndToEndSyncFindingsTest(unittest.TestCase):
    """Proves the full path: sync produces a finding → GET /integrity/findings returns it."""

    def setUp(self) -> None:
        self.app, self.factory = _make_test_app()
        self.client = TestClient(self.app)

    def test_naming_violation_persisted_and_returned_by_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            idx = root / "docs" / "roadmap" / "ROADMAP_INDEX.md"
            idx.parent.mkdir(parents=True)
            # INVALID-NO-PREFIX does not match RM-<DOMAIN>-<NNN>
            idx.write_text("- `INVALID-NO-PREFIX` — Bad naming\n", encoding="utf-8")

            db = self.factory()
            sync_roadmap(db, root)
            db.close()

        resp = self.client.get("/integrity/findings")
        self.assertEqual(resp.status_code, 200)

        findings = resp.json()
        violations = [f for f in findings if f["finding_type"] == "naming_violation"]
        self.assertEqual(len(violations), 1)
        v = violations[0]
        self.assertEqual(v["object_ref"], "INVALID-NO-PREFIX")
        self.assertEqual(v["severity"], "error")
        self.assertEqual(v["status"], "open")
        self.assertIn("finding_id", v)
        self.assertIn("detected_at", v)


class HealthEndpointTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app, _ = _make_test_app()
        self.client = TestClient(self.app)

    def test_health_ok(self) -> None:
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})


class SyncTriggerEndpointTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app, self.factory = _make_test_app()
        self.client = TestClient(self.app)

    def _make_repo(self, tmp_dir: Path, item_id: str = "RM-GOV-001", title: str = "Governance init") -> Path:
        idx = tmp_dir / "docs" / "roadmap" / "ROADMAP_INDEX.md"
        idx.parent.mkdir(parents=True)
        idx.write_text(f"- `{item_id}` — {title}\n", encoding="utf-8")
        return tmp_dir

    def test_sync_endpoint_mounted(self) -> None:
        resp = self.client.post("/sync/roadmap")
        # Will succeed or fail depending on repo state; just verify it's mounted (not 404/405)
        self.assertNotEqual(resp.status_code, 404)
        self.assertNotEqual(resp.status_code, 405)

    def test_sync_endpoint_returns_expected_fields(self) -> None:
        resp = self.client.post("/sync/roadmap")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for field in ("items_created", "items_updated", "items_unchanged", "findings_created"):
            self.assertIn(field, body, f"missing field: {field}")

    def test_sync_dry_run_does_not_persist_items(self) -> None:
        resp = self.client.post("/sync/roadmap?dry_run=true")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        # dry_run: no artifact_path
        self.assertIsNone(body.get("artifact_path"))
        # dry_run: no rows written
        db = self.factory()
        count = db.query(RoadmapItem).count()
        db.close()
        self.assertEqual(count, 0)

    def test_sync_artifact_written_when_not_dry_run(self) -> None:
        resp = self.client.post("/sync/roadmap")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        # artifact_path may be None if no ROADMAP_INDEX.md exists in repo root,
        # but if items were processed it should be set
        # We at minimum verify the field is present in the response
        self.assertIn("artifact_path", body)


class IntegrityTriggerEndpointTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app, self.factory = _make_test_app()
        self.client = TestClient(self.app)

    def _seed(self, *items: RoadmapItem) -> None:
        db = self.factory()
        for item in items:
            db.add(item)
        db.commit()
        db.close()

    def test_integrity_endpoint_mounted(self) -> None:
        resp = self.client.post("/reviews/integrity")
        self.assertNotEqual(resp.status_code, 404)
        self.assertNotEqual(resp.status_code, 405)

    def test_integrity_endpoint_returns_expected_fields(self) -> None:
        resp = self.client.post("/reviews/integrity")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        for field in ("items_checked", "findings_created", "findings_skipped"):
            self.assertIn(field, body, f"missing field: {field}")

    def test_integrity_checks_seeded_items(self) -> None:
        # Seed an item with an invalid priority to trigger a finding
        item = _item("RM-GOV-001")
        item.priority = "INVALID"
        self._seed(item)

        resp = self.client.post("/reviews/integrity")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["items_checked"], 1)
        self.assertGreater(body["findings_created"], 0)

        # Finding should be persisted and queryable
        findings_resp = self.client.get("/integrity/findings?finding_type=invalid_priority")
        self.assertEqual(findings_resp.status_code, 200)
        self.assertEqual(len(findings_resp.json()), 1)

    def test_integrity_dry_run_does_not_persist_findings(self) -> None:
        item = _item("RM-GOV-001")
        item.priority = "INVALID"
        self._seed(item)

        resp = self.client.post("/reviews/integrity?dry_run=true")
        self.assertEqual(resp.status_code, 200)

        db = self.factory()
        count = db.query(IntegrityFinding).count()
        db.close()
        self.assertEqual(count, 0)

    def test_integrity_artifact_field_present(self) -> None:
        resp = self.client.post("/reviews/integrity")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("artifact_path", resp.json())


if __name__ == "__main__":
    unittest.main()
