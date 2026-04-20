"""Offline tests for RGC API endpoints.

Uses FastAPI TestClient with an in-memory SQLite override.
"""

from __future__ import annotations

import sys
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


if __name__ == "__main__":
    unittest.main()
