"""Offline tests for RGC Slice 2: integrity review service and lifecycle API."""

from __future__ import annotations

import json
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
from roadmap_governance.integrity import (
    NEAR_DUPLICATE_THRESHOLD,
    VALID_CATEGORIES,
    VALID_ITEM_TYPES,
    VALID_PRIORITIES,
    run_integrity_review,
)
from roadmap_governance.models import Base, IntegrityFinding, RoadmapItem
from roadmap_governance.router import router as rgc_router


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _make_session_factory(engine):
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _make_test_app():
    engine = _make_engine()
    factory = _make_session_factory(engine)

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


def _item(
    item_id: str,
    title: str = "A Valid Title",
    category: str = "GOV",
    priority: str = "P2",
    item_type: str = "governance",
    status: str = "proposed",
) -> RoadmapItem:
    now = _now()
    return RoadmapItem(
        id=item_id,
        title=title,
        category=category,
        item_type=item_type,
        priority=priority,
        status=status,
        description=None,
        source_path="docs/roadmap/ROADMAP_INDEX.md",
        source_hash="abc123",
        naming_version="v1",
        created_at=now,
        updated_at=now,
    )


def _seed(factory, *items: RoadmapItem) -> None:
    db = factory()
    for item in items:
        db.add(item)
    db.commit()
    db.close()


# ── Token validation tests ───────────────────────────────────────────────────

class InvalidPriorityTest(unittest.TestCase):
    def setUp(self):
        engine = _make_engine()
        self.factory = _make_session_factory(engine)

    def test_invalid_priority_raises_finding(self):
        _seed(self.factory, _item("RM-GOV-001", priority="BADPRI"))
        db = self.factory()
        result = run_integrity_review(db, REPO_ROOT)
        db.close()
        self.assertGreater(result.findings_created, 0)
        self.assertIn("invalid_priority", result.check_counts)

    def test_valid_priorities_no_finding(self):
        for p in VALID_PRIORITIES:
            engine = _make_engine()
            factory = _make_session_factory(engine)
            _seed(factory, _item("RM-GOV-001", priority=p))
            db = factory()
            result = run_integrity_review(db, REPO_ROOT)
            db.close()
            self.assertNotIn("invalid_priority", result.check_counts, f"priority {p} flagged")


class InvalidItemTypeTest(unittest.TestCase):
    def setUp(self):
        engine = _make_engine()
        self.factory = _make_session_factory(engine)

    def test_invalid_item_type_raises_finding(self):
        _seed(self.factory, _item("RM-GOV-001", item_type="mystery_type"))
        db = self.factory()
        result = run_integrity_review(db, REPO_ROOT)
        db.close()
        self.assertIn("invalid_item_type", result.check_counts)

    def test_unknown_item_type_exempt(self):
        _seed(self.factory, _item("RM-GOV-001", item_type="unknown"))
        db = self.factory()
        result = run_integrity_review(db, REPO_ROOT)
        db.close()
        self.assertNotIn("invalid_item_type", result.check_counts)

    def test_valid_item_types_no_finding(self):
        for t in list(VALID_ITEM_TYPES)[:3]:
            engine = _make_engine()
            factory = _make_session_factory(engine)
            _seed(factory, _item("RM-GOV-001", item_type=t))
            db = factory()
            result = run_integrity_review(db, REPO_ROOT)
            db.close()
            self.assertNotIn("invalid_item_type", result.check_counts, f"type {t} flagged")


class InvalidCategoryTest(unittest.TestCase):
    def setUp(self):
        engine = _make_engine()
        self.factory = _make_session_factory(engine)

    def test_invalid_category_raises_finding(self):
        _seed(self.factory, _item("RM-GOV-001", category="FAKECAT"))
        db = self.factory()
        result = run_integrity_review(db, REPO_ROOT)
        db.close()
        self.assertIn("invalid_category", result.check_counts)

    def test_valid_categories_no_finding(self):
        for cat in list(VALID_CATEGORIES)[:3]:
            engine = _make_engine()
            factory = _make_session_factory(engine)
            _seed(factory, _item("RM-GOV-001", category=cat))
            db = factory()
            result = run_integrity_review(db, REPO_ROOT)
            db.close()
            self.assertNotIn("invalid_category", result.check_counts, f"category {cat} flagged")


class NamingViolationIntegrityTest(unittest.TestCase):
    def setUp(self):
        engine = _make_engine()
        self.factory = _make_session_factory(engine)

    def test_bad_id_raises_finding(self):
        _seed(self.factory, _item("BADID-001"))
        db = self.factory()
        result = run_integrity_review(db, REPO_ROOT)
        db.close()
        self.assertIn("naming_violation", result.check_counts)

    def test_good_id_no_naming_finding(self):
        _seed(self.factory, _item("RM-GOV-001"))
        db = self.factory()
        result = run_integrity_review(db, REPO_ROOT)
        db.close()
        self.assertNotIn("naming_violation", result.check_counts)


# ── Near-duplicate title tests ────────────────────────────────────────────────

class NearDuplicateTitleTest(unittest.TestCase):
    def setUp(self):
        engine = _make_engine()
        self.factory = _make_session_factory(engine)

    def _run(self) -> int:
        db = self.factory()
        result = run_integrity_review(db, REPO_ROOT)
        db.close()
        return result.check_counts.get("near_duplicate_title", 0)

    def test_identical_titles_flagged(self):
        _seed(
            self.factory,
            _item("RM-GOV-001", title="Implement authentication service"),
            _item("RM-GOV-002", title="Implement authentication service"),
        )
        self.assertEqual(self._run(), 1)

    def test_very_similar_titles_flagged(self):
        _seed(
            self.factory,
            _item("RM-GOV-001", title="Implement the authentication service"),
            _item("RM-GOV-002", title="Implement authentication services"),
        )
        self.assertEqual(self._run(), 1)

    def test_distinct_titles_not_flagged(self):
        _seed(
            self.factory,
            _item("RM-GOV-001", title="Build authentication layer"),
            _item("RM-GOV-002", title="Deploy monitoring dashboards"),
        )
        self.assertEqual(self._run(), 0)

    def test_three_items_two_near_dups(self):
        _seed(
            self.factory,
            _item("RM-GOV-001", title="Implement authentication service"),
            _item("RM-GOV-002", title="Implement authentication service"),
            _item("RM-GOV-003", title="Deploy monitoring dashboards"),
        )
        self.assertEqual(self._run(), 1)


# ── Idempotence tests ─────────────────────────────────────────────────────────

class IdempotenceTest(unittest.TestCase):
    def setUp(self):
        engine = _make_engine()
        self.factory = _make_session_factory(engine)
        _seed(self.factory, _item("RM-GOV-001", priority="BADPRI"))

    def test_second_run_does_not_duplicate(self):
        db = self.factory()
        r1 = run_integrity_review(db, REPO_ROOT)
        db.close()

        db = self.factory()
        r2 = run_integrity_review(db, REPO_ROOT)
        db.close()

        self.assertGreater(r1.findings_created, 0)
        self.assertEqual(r2.findings_created, 0)
        self.assertGreater(r2.findings_skipped, 0)

    def test_accepted_finding_not_recreated(self):
        db = self.factory()
        run_integrity_review(db, REPO_ROOT)
        # Accept the finding
        finding = db.query(IntegrityFinding).filter_by(finding_type="invalid_priority").first()
        finding.status = "accepted"
        db.commit()
        db.close()

        db = self.factory()
        r2 = run_integrity_review(db, REPO_ROOT)
        db.close()
        self.assertEqual(r2.findings_created, 0)

    def test_suppressed_finding_not_recreated(self):
        db = self.factory()
        run_integrity_review(db, REPO_ROOT)
        finding = db.query(IntegrityFinding).filter_by(finding_type="invalid_priority").first()
        finding.status = "suppressed"
        db.commit()
        db.close()

        db = self.factory()
        r2 = run_integrity_review(db, REPO_ROOT)
        db.close()
        self.assertEqual(r2.findings_created, 0)

    def test_resolved_finding_reraises(self):
        db = self.factory()
        run_integrity_review(db, REPO_ROOT)
        finding = db.query(IntegrityFinding).filter_by(finding_type="invalid_priority").first()
        finding.status = "resolved"
        db.commit()
        db.close()

        # Issue still present → should be re-raised
        db = self.factory()
        r2 = run_integrity_review(db, REPO_ROOT)
        db.close()
        self.assertGreater(r2.findings_created, 0)


# ── Artifact writing tests ────────────────────────────────────────────────────

class ArtifactWritingTest(unittest.TestCase):
    def setUp(self):
        engine = _make_engine()
        self.factory = _make_session_factory(engine)
        _seed(self.factory, _item("RM-GOV-001"))

    def test_artifact_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            art_dir = Path(tmp) / "integrity"
            db = self.factory()
            result = run_integrity_review(db, REPO_ROOT, artifact_dir=art_dir)
            db.close()

            self.assertIsNotNone(result.artifact_path)
            self.assertTrue(Path(result.artifact_path).exists())

            latest = art_dir / "latest.json"
            self.assertTrue(latest.exists())

            payload = json.loads(latest.read_text())
            self.assertIn("generated_at", payload)
            self.assertIn("items_checked", payload)
            self.assertEqual(payload["items_checked"], 1)

    def test_dry_run_no_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            art_dir = Path(tmp) / "integrity"
            db = self.factory()
            result = run_integrity_review(db, REPO_ROOT, artifact_dir=art_dir, dry_run=True)
            db.close()
            self.assertIsNone(result.artifact_path)
            self.assertFalse(art_dir.exists())

    def test_artifact_is_valid_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            art_dir = Path(tmp) / "integrity"
            db = self.factory()
            result = run_integrity_review(db, REPO_ROOT, artifact_dir=art_dir)
            db.close()
            payload = json.loads(Path(result.artifact_path).read_text())
            for key in ("generated_at", "items_checked", "findings_created", "findings_skipped", "check_counts"):
                self.assertIn(key, payload)


# ── Lifecycle API tests ───────────────────────────────────────────────────────

class FindingGetByIdTest(unittest.TestCase):
    def setUp(self):
        self.app, self.factory = _make_test_app()
        self.client = TestClient(self.app)

    def _seed_finding(self) -> str:
        fid = str(uuid.uuid4())
        db = self.factory()
        db.add(IntegrityFinding(
            finding_id=fid,
            finding_type="invalid_priority",
            severity="warning",
            object_type="roadmap_item",
            object_ref="RM-GOV-001",
            summary="Bad priority",
            details={},
            detected_at=_now(),
            status="open",
            resolution_note=None,
        ))
        db.commit()
        db.close()
        return fid

    def test_get_existing_finding(self):
        fid = self._seed_finding()
        resp = self.client.get(f"/integrity/findings/{fid}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["finding_id"], fid)

    def test_get_nonexistent_returns_404(self):
        resp = self.client.get(f"/integrity/findings/{uuid.uuid4()}")
        self.assertEqual(resp.status_code, 404)


class FindingLifecyclePatchTest(unittest.TestCase):
    def setUp(self):
        self.app, self.factory = _make_test_app()
        self.client = TestClient(self.app)

    def _seed_finding(self, status: str = "open") -> str:
        fid = str(uuid.uuid4())
        db = self.factory()
        db.add(IntegrityFinding(
            finding_id=fid,
            finding_type="invalid_priority",
            severity="warning",
            object_type="roadmap_item",
            object_ref="RM-GOV-001",
            summary="Bad priority",
            details={},
            detected_at=_now(),
            status=status,
            resolution_note=None,
        ))
        db.commit()
        db.close()
        return fid

    def test_resolve_finding(self):
        fid = self._seed_finding()
        resp = self.client.patch(f"/integrity/findings/{fid}", json={"status": "resolved"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "resolved")

    def test_accept_finding(self):
        fid = self._seed_finding()
        resp = self.client.patch(f"/integrity/findings/{fid}", json={"status": "accepted"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "accepted")

    def test_suppress_with_note(self):
        fid = self._seed_finding()
        resp = self.client.patch(
            f"/integrity/findings/{fid}",
            json={"status": "suppressed", "resolution_note": "Intentional legacy value"},
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["status"], "suppressed")
        self.assertEqual(body["resolution_note"], "Intentional legacy value")

    def test_patch_nonexistent_returns_404(self):
        resp = self.client.patch(
            f"/integrity/findings/{uuid.uuid4()}",
            json={"status": "resolved"},
        )
        self.assertEqual(resp.status_code, 404)

    def test_invalid_status_rejected(self):
        fid = self._seed_finding()
        resp = self.client.patch(f"/integrity/findings/{fid}", json={"status": "deleted"})
        self.assertEqual(resp.status_code, 422)

    def test_status_persists_across_get(self):
        fid = self._seed_finding()
        self.client.patch(f"/integrity/findings/{fid}", json={"status": "accepted"})
        resp = self.client.get(f"/integrity/findings/{fid}")
        self.assertEqual(resp.json()["status"], "accepted")


class EndToEndIntegrityRunToApiTest(unittest.TestCase):
    """Proves: run_integrity_review() persists findings → GET /integrity/findings returns them."""

    def setUp(self):
        self.app, self.factory = _make_test_app()
        self.client = TestClient(self.app)

    def test_integrity_findings_visible_via_api(self):
        _seed(
            self.factory,
            _item("RM-GOV-001", priority="BADPRI"),
            _item("RM-GOV-002", category="FAKECAT"),
        )
        db = self.factory()
        run_integrity_review(db, REPO_ROOT)
        db.close()

        resp = self.client.get("/integrity/findings")
        self.assertEqual(resp.status_code, 200)
        findings = resp.json()
        types = {f["finding_type"] for f in findings}
        self.assertIn("invalid_priority", types)
        self.assertIn("invalid_category", types)
        for f in findings:
            self.assertEqual(f["status"], "open")
            self.assertIn("finding_id", f)
            self.assertIn("detected_at", f)

    def test_lifecycle_patch_after_integrity_run(self):
        _seed(self.factory, _item("RM-GOV-001", priority="BADPRI"))
        db = self.factory()
        run_integrity_review(db, REPO_ROOT)
        db.close()

        resp = self.client.get("/integrity/findings?finding_type=invalid_priority")
        self.assertEqual(resp.status_code, 200)
        findings = resp.json()
        self.assertEqual(len(findings), 1)
        fid = findings[0]["finding_id"]

        patch = self.client.patch(f"/integrity/findings/{fid}", json={"status": "accepted", "resolution_note": "P9 intentional"})
        self.assertEqual(patch.status_code, 200)
        self.assertEqual(patch.json()["status"], "accepted")

        get = self.client.get(f"/integrity/findings/{fid}")
        self.assertEqual(get.json()["status"], "accepted")
        self.assertEqual(get.json()["resolution_note"], "P9 intentional")


if __name__ == "__main__":
    unittest.main()
