"""Offline tests for RGC Slice 3: CMDB registry and import."""

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

from roadmap_governance.cmdb_service import (
    VALID_ENTITY_TYPES,
    import_cmdb_entities,
    validate_canonical_name,
)
from roadmap_governance.database import get_db_dep
from roadmap_governance.models import Base, CmdbEntity, IntegrityFinding
from roadmap_governance.router import router as rgc_router


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _make_factory(engine):
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def _make_test_app():
    engine = _make_engine()
    factory = _make_factory(engine)

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


def _entity_dict(
    canonical_name: str = "homelab.main.host01",
    entity_type: str = "machine",
    display_name: str = "Host 01",
    environment: str = "homelab",
    **kwargs,
) -> dict:
    d = {
        "canonical_name": canonical_name,
        "entity_type": entity_type,
        "display_name": display_name,
        "environment": environment,
    }
    d.update(kwargs)
    return d


def _seed_entity(
    factory,
    canonical_name: str = "homelab.main.host01",
    entity_type: str = "machine",
    environment: str = "homelab",
) -> str:
    eid = str(uuid.uuid4())
    now = _now()
    db = factory()
    db.add(CmdbEntity(
        entity_id=eid,
        entity_type=entity_type,
        canonical_name=canonical_name,
        display_name="Test Entity",
        platform=None,
        environment=environment,
        criticality=None,
        owner=None,
        lifecycle_state=None,
        source_system="seed_file",
        external_ref=None,
        entity_metadata={},
        created_at=now,
        updated_at=now,
    ))
    db.commit()
    db.close()
    return eid


# ── canonical name validation ────────────────────────────────────────────────

class CanonicalNameValidationTest(unittest.TestCase):
    def test_valid_three_segment(self):
        self.assertTrue(validate_canonical_name("homelab.main.compute01"))

    def test_valid_two_segment(self):
        self.assertTrue(validate_canonical_name("prod.api"))

    def test_valid_with_hyphens(self):
        self.assertTrue(validate_canonical_name("prod.my-service.api-v2"))

    def test_invalid_uppercase(self):
        self.assertFalse(validate_canonical_name("Prod.Main.Host"))

    def test_invalid_single_segment(self):
        self.assertFalse(validate_canonical_name("hostname"))

    def test_invalid_empty(self):
        self.assertFalse(validate_canonical_name(""))

    def test_invalid_trailing_dot(self):
        self.assertFalse(validate_canonical_name("prod.api."))

    def test_invalid_leading_hyphen_segment(self):
        self.assertFalse(validate_canonical_name("prod.-api"))

    def test_invalid_spaces(self):
        self.assertFalse(validate_canonical_name("prod.my service"))


# ── import service tests ──────────────────────────────────────────────────────

class ValidImportTest(unittest.TestCase):
    def setUp(self):
        engine = _make_engine()
        self.factory = _make_factory(engine)

    def test_creates_entities(self):
        entities = [
            _entity_dict("homelab.main.compute01", "machine"),
            _entity_dict("prod.rgc.api", "service", display_name="RGC API", environment="prod"),
        ]
        db = self.factory()
        result = import_cmdb_entities(db, entities)
        db.close()
        self.assertEqual(result.entities_created, 2)
        self.assertEqual(result.entities_updated, 0)
        self.assertEqual(result.entities_unchanged, 0)
        self.assertEqual(result.findings_created, 0)

    def test_all_entity_types_accepted(self):
        entities = [
            _entity_dict(f"test.{t}.instance", t)
            for t in VALID_ENTITY_TYPES
        ]
        db = self.factory()
        result = import_cmdb_entities(db, entities)
        db.close()
        self.assertEqual(result.entities_created, len(VALID_ENTITY_TYPES))
        self.assertEqual(result.findings_created, 0)

    def test_metadata_persisted(self):
        db = self.factory()
        import_cmdb_entities(db, [_entity_dict(metadata={"os": "ubuntu", "roles": ["coding"]})])
        row = db.query(CmdbEntity).filter_by(canonical_name="homelab.main.host01").first()
        db.close()
        self.assertEqual(row.entity_metadata["os"], "ubuntu")

    def test_source_system_defaults_to_seed_file(self):
        db = self.factory()
        import_cmdb_entities(db, [_entity_dict()])
        row = db.query(CmdbEntity).filter_by(canonical_name="homelab.main.host01").first()
        db.close()
        self.assertEqual(row.source_system, "seed_file")


class InvalidCanonicalNameTest(unittest.TestCase):
    def setUp(self):
        engine = _make_engine()
        self.factory = _make_factory(engine)

    def test_bad_name_produces_finding(self):
        db = self.factory()
        result = import_cmdb_entities(db, [_entity_dict("BADNAME")])
        db.close()
        self.assertGreater(result.findings_created, 0)

    def test_bad_name_finding_type(self):
        db = self.factory()
        import_cmdb_entities(db, [_entity_dict("BADNAME")])
        finding = db.query(IntegrityFinding).filter_by(finding_type="invalid_canonical_name").first()
        db.close()
        self.assertIsNotNone(finding)
        self.assertEqual(finding.status, "open")
        self.assertEqual(finding.severity, "error")

    def test_empty_name_skips_upsert(self):
        db = self.factory()
        result = import_cmdb_entities(db, [_entity_dict("")])
        db.close()
        self.assertEqual(result.entities_created, 0)
        self.assertGreater(result.findings_created, 0)

    def test_valid_name_no_finding(self):
        db = self.factory()
        result = import_cmdb_entities(db, [_entity_dict("prod.rgc.api")])
        db.close()
        self.assertEqual(result.findings_created, 0)


class InvalidEntityTypeTest(unittest.TestCase):
    def setUp(self):
        engine = _make_engine()
        self.factory = _make_factory(engine)

    def test_bad_entity_type_produces_finding(self):
        db = self.factory()
        result = import_cmdb_entities(db, [_entity_dict(entity_type="unknown_type")])
        db.close()
        self.assertGreater(result.findings_created, 0)

    def test_bad_entity_type_finding_type(self):
        db = self.factory()
        import_cmdb_entities(db, [_entity_dict(entity_type="unknown_type")])
        finding = db.query(IntegrityFinding).filter_by(finding_type="invalid_entity_type").first()
        db.close()
        self.assertIsNotNone(finding)
        self.assertEqual(finding.severity, "warning")

    def test_bad_entity_type_still_upserts(self):
        db = self.factory()
        result = import_cmdb_entities(db, [_entity_dict(entity_type="unknown_type")])
        db.close()
        # Entity is still upserted even with a bad type (finding records the issue).
        self.assertEqual(result.entities_created, 1)


class DuplicateCanonicalNameTest(unittest.TestCase):
    def setUp(self):
        engine = _make_engine()
        self.factory = _make_factory(engine)

    def test_duplicate_in_batch_produces_finding(self):
        entities = [
            _entity_dict("prod.rgc.api"),
            _entity_dict("prod.rgc.api", display_name="RGC API v2"),
        ]
        db = self.factory()
        result = import_cmdb_entities(db, entities)
        db.close()
        self.assertGreater(result.findings_created, 0)

    def test_only_first_occurrence_upserted(self):
        entities = [
            _entity_dict("prod.rgc.api", display_name="First"),
            _entity_dict("prod.rgc.api", display_name="Second"),
        ]
        db = self.factory()
        result = import_cmdb_entities(db, entities)
        db.close()
        self.assertEqual(result.entities_created, 1)
        row = db.query(CmdbEntity).filter_by(canonical_name="prod.rgc.api").first()
        self.assertEqual(row.display_name, "First")
        db.close()

    def test_duplicate_finding_type_and_severity(self):
        entities = [_entity_dict("prod.rgc.api"), _entity_dict("prod.rgc.api")]
        db = self.factory()
        import_cmdb_entities(db, entities)
        finding = db.query(IntegrityFinding).filter_by(finding_type="duplicate_canonical_name").first()
        db.close()
        self.assertIsNotNone(finding)
        self.assertEqual(finding.severity, "warning")


class IdempotentReimportTest(unittest.TestCase):
    def setUp(self):
        engine = _make_engine()
        self.factory = _make_factory(engine)
        self.entities = [
            _entity_dict("homelab.main.compute01", "machine"),
            _entity_dict("prod.rgc.api", "service"),
        ]

    def test_second_import_unchanged(self):
        db = self.factory()
        import_cmdb_entities(db, self.entities)
        db.close()

        db = self.factory()
        r2 = import_cmdb_entities(db, self.entities)
        db.close()
        self.assertEqual(r2.entities_created, 0)
        self.assertEqual(r2.entities_updated, 0)
        self.assertEqual(r2.entities_unchanged, 2)
        self.assertEqual(r2.findings_created, 0)

    def test_changed_field_triggers_update(self):
        db = self.factory()
        import_cmdb_entities(db, self.entities)
        db.close()

        modified = [
            _entity_dict("homelab.main.compute01", "machine", display_name="Updated Name"),
            _entity_dict("prod.rgc.api", "service"),
        ]
        db = self.factory()
        r2 = import_cmdb_entities(db, modified)
        db.close()
        self.assertEqual(r2.entities_updated, 1)
        self.assertEqual(r2.entities_unchanged, 1)

    def test_dry_run_does_not_write(self):
        db = self.factory()
        r = import_cmdb_entities(db, self.entities, dry_run=True)
        count = db.query(CmdbEntity).count()
        db.close()
        self.assertEqual(count, 0)
        self.assertEqual(r.entities_created, 2)

    def test_finding_not_duplicated_on_rerun(self):
        bad = [_entity_dict("BADNAME")]
        db = self.factory()
        r1 = import_cmdb_entities(db, bad)
        db.close()

        db = self.factory()
        r2 = import_cmdb_entities(db, bad)
        db.close()
        self.assertGreater(r1.findings_created, 0)
        self.assertEqual(r2.findings_created, 0)


# ── API endpoint tests ────────────────────────────────────────────────────────

class CmdbEntityListEndpointTest(unittest.TestCase):
    def setUp(self):
        self.app, self.factory = _make_test_app()
        self.client = TestClient(self.app)

    def test_empty_returns_list(self):
        resp = self.client.get("/cmdb/entities")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_returns_seeded_entities(self):
        _seed_entity(self.factory, "homelab.main.host01", "machine")
        _seed_entity(self.factory, "prod.rgc.api", "service")
        resp = self.client.get("/cmdb/entities")
        self.assertEqual(resp.status_code, 200)
        names = {r["canonical_name"] for r in resp.json()}
        self.assertIn("homelab.main.host01", names)
        self.assertIn("prod.rgc.api", names)

    def test_filter_by_entity_type(self):
        _seed_entity(self.factory, "homelab.main.host01", "machine")
        _seed_entity(self.factory, "prod.rgc.api", "service")
        resp = self.client.get("/cmdb/entities?entity_type=machine")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["entity_type"], "machine")

    def test_filter_by_environment(self):
        _seed_entity(self.factory, "homelab.main.host01", "machine", environment="homelab")
        _seed_entity(self.factory, "prod.rgc.api", "service", environment="prod")
        resp = self.client.get("/cmdb/entities?environment=homelab")
        self.assertEqual(resp.status_code, 200)
        names = [r["canonical_name"] for r in resp.json()]
        self.assertIn("homelab.main.host01", names)
        self.assertNotIn("prod.rgc.api", names)

    def test_response_fields_present(self):
        _seed_entity(self.factory, "homelab.main.host01")
        resp = self.client.get("/cmdb/entities")
        row = resp.json()[0]
        for field in (
            "entity_id", "entity_type", "canonical_name", "display_name",
            "environment", "metadata", "created_at", "updated_at",
        ):
            self.assertIn(field, row, f"missing field: {field}")

    def test_ordered_by_canonical_name(self):
        _seed_entity(self.factory, "prod.z.host")
        _seed_entity(self.factory, "prod.a.host")
        _seed_entity(self.factory, "homelab.main.host")
        resp = self.client.get("/cmdb/entities")
        names = [r["canonical_name"] for r in resp.json()]
        self.assertEqual(names, sorted(names))


class CmdbEntityDetailEndpointTest(unittest.TestCase):
    def setUp(self):
        self.app, self.factory = _make_test_app()
        self.client = TestClient(self.app)

    def test_get_existing_entity(self):
        eid = _seed_entity(self.factory, "homelab.main.host01")
        resp = self.client.get(f"/cmdb/entities/{eid}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["entity_id"], eid)
        self.assertEqual(resp.json()["canonical_name"], "homelab.main.host01")

    def test_get_nonexistent_returns_404(self):
        resp = self.client.get(f"/cmdb/entities/{uuid.uuid4()}")
        self.assertEqual(resp.status_code, 404)


class EndToEndCmdbImportToApiTest(unittest.TestCase):
    """Proves: import_cmdb_entities → GET /cmdb/entities returns persisted entities."""

    def setUp(self):
        self.app, self.factory = _make_test_app()
        self.client = TestClient(self.app)

    def test_imported_entities_visible_via_api(self):
        entities = [
            _entity_dict("homelab.main.compute01", "machine"),
            _entity_dict("prod.rgc.api", "service"),
        ]
        db = self.factory()
        import_cmdb_entities(db, entities)
        db.close()

        resp = self.client.get("/cmdb/entities")
        self.assertEqual(resp.status_code, 200)
        names = {r["canonical_name"] for r in resp.json()}
        self.assertIn("homelab.main.compute01", names)
        self.assertIn("prod.rgc.api", names)

    def test_import_findings_visible_via_integrity_api(self):
        db = self.factory()
        import_cmdb_entities(db, [_entity_dict("BADNAME")])
        db.close()

        resp = self.client.get("/integrity/findings?finding_type=invalid_canonical_name")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        f = resp.json()[0]
        self.assertEqual(f["object_type"], "cmdb_entity")
        self.assertEqual(f["status"], "open")


class SeedFileLoadTest(unittest.TestCase):
    """Tests load_seed_file with actual YAML content."""

    def test_loads_example_seed(self):
        from roadmap_governance.cmdb_service import load_seed_file
        content = """
entities:
  - entity_type: machine
    canonical_name: homelab.main.compute01
    display_name: Main Compute 01
    environment: homelab
    criticality: high
    metadata:
      os: ubuntu
      roles: [coding, inference]

  - entity_type: service
    canonical_name: prod.rgc.api
    display_name: Roadmap Governance API
    environment: prod
    owner: platform
    metadata:
      protocol: http
      port: 8000
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            f.write(content)
            tmp_path = Path(f.name)

        try:
            entities = load_seed_file(tmp_path)
            self.assertEqual(len(entities), 2)
            self.assertEqual(entities[0]["canonical_name"], "homelab.main.compute01")
            self.assertEqual(entities[1]["entity_type"], "service")
        finally:
            tmp_path.unlink()

    def test_full_seed_import(self):
        from roadmap_governance.cmdb_service import load_seed_file
        content = """
entities:
  - entity_type: machine
    canonical_name: homelab.main.compute01
    display_name: Main Compute 01
    environment: homelab
  - entity_type: service
    canonical_name: prod.rgc.api
    display_name: RGC API
    environment: prod
"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            f.write(content)
            tmp_path = Path(f.name)

        engine = _make_engine()
        factory = _make_factory(engine)
        try:
            entities = load_seed_file(tmp_path)
            db = factory()
            result = import_cmdb_entities(db, entities)
            db.close()
            self.assertEqual(result.entities_created, 2)
            self.assertEqual(result.findings_created, 0)
        finally:
            tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
