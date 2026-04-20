"""Offline tests for roadmap_governance/service.py.

All tests use an in-memory SQLite database — no external services required.
"""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from roadmap_governance.models import Base, IntegrityFinding, RoadmapItem
from roadmap_governance.service import sync_roadmap


def _make_session():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return factory()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


_ITEM_YAML = """\
schema_version: "1.0"
kind: "roadmap_item"
id: "{id}"
title: "{title}"
category: "{category}"
type: "governance"
status: "proposed"
priority: "P1"
description: "Test item."
"""


class SyncBasicTest(unittest.TestCase):
    def _repo_with_md(self, md_text: str, yaml_items: dict | None = None):
        """Return a (tmpdir, repo_root) pair with the given markdown and optional YAMLs."""
        tmp = tempfile.mkdtemp()
        root = Path(tmp)
        _write(root / "docs" / "roadmap" / "ROADMAP_INDEX.md", md_text)
        if yaml_items:
            for item_id, data in yaml_items.items():
                content = _ITEM_YAML.format(
                    id=item_id,
                    title=data.get("title", item_id),
                    category=data.get("category", "GOV"),
                )
                _write(root / "docs" / "roadmap" / "items" / f"{item_id}.yaml", content)
        return tmp, root

    def test_creates_items_from_markdown(self) -> None:
        md = "- `RM-GOV-002` — Reconcile source\n- `RM-GOV-003` — Create ADRs\n"
        _, root = self._repo_with_md(md)
        db = _make_session()
        result = sync_roadmap(db, root)
        self.assertEqual(result.items_created, 2)
        self.assertEqual(result.items_updated, 0)
        self.assertEqual(db.query(RoadmapItem).count(), 2)

    def test_idempotent_rerun(self) -> None:
        md = "- `RM-GOV-002` — Reconcile source\n"
        _, root = self._repo_with_md(md)
        db = _make_session()
        r1 = sync_roadmap(db, root)
        r2 = sync_roadmap(db, root)
        self.assertEqual(r1.items_created, 1)
        self.assertEqual(r2.items_created, 0)
        self.assertEqual(r2.items_unchanged, 1)
        # Findings also not duplicated on rerun
        self.assertEqual(r1.findings_created, r2.findings_created)

    def test_upsert_updates_changed_title(self) -> None:
        md = "- `RM-GOV-002` — Original title\n"
        _, root = self._repo_with_md(md)
        db = _make_session()
        sync_roadmap(db, root)

        # Change the markdown title
        _write(root / "docs" / "roadmap" / "ROADMAP_INDEX.md",
               "- `RM-GOV-002` — New title\n")
        result = sync_roadmap(db, root)
        self.assertEqual(result.items_updated, 1)
        item = db.query(RoadmapItem).filter_by(id="RM-GOV-002").one()
        self.assertEqual(item.title, "New title")

    def test_yaml_enriched_item_uses_yaml_fields(self) -> None:
        md = "- `RM-GOV-002` — Markdown title\n"
        _, root = self._repo_with_md(
            md,
            yaml_items={"RM-GOV-002": {"title": "YAML title", "category": "GOV"}},
        )
        db = _make_session()
        sync_roadmap(db, root)
        item = db.query(RoadmapItem).filter_by(id="RM-GOV-002").one()
        self.assertEqual(item.title, "YAML title")
        self.assertEqual(item.priority, "P1")
        self.assertEqual(item.item_type, "governance")


class FindingsDuplicateTest(unittest.TestCase):
    def test_duplicate_id_creates_finding(self) -> None:
        md = (
            "- `RM-GOV-002` — First\n"
            "- `RM-GOV-002` — Duplicate\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "docs" / "roadmap" / "ROADMAP_INDEX.md", md)
            db = _make_session()
            result = sync_roadmap(db, root)
        self.assertGreaterEqual(result.findings_created, 1)
        finding = (
            db.query(IntegrityFinding)
            .filter_by(finding_type="duplicate_id", object_ref="RM-GOV-002")
            .first()
        )
        self.assertIsNotNone(finding)
        self.assertEqual(finding.severity, "warning")
        self.assertEqual(finding.status, "open")

    def test_duplicate_finding_not_doubled_on_rerun(self) -> None:
        md = "- `RM-GOV-002` — First\n- `RM-GOV-002` — Dup\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "docs" / "roadmap" / "ROADMAP_INDEX.md", md)
            db = _make_session()
            r1 = sync_roadmap(db, root)
            r2 = sync_roadmap(db, root)
        count = (
            db.query(IntegrityFinding)
            .filter_by(finding_type="duplicate_id", object_ref="RM-GOV-002")
            .count()
        )
        self.assertEqual(count, 1)
        self.assertEqual(r2.findings_created, 0)


class FindingsNamingTest(unittest.TestCase):
    def test_bad_id_creates_naming_violation(self) -> None:
        md = "- `BADID` — Missing prefix\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "docs" / "roadmap" / "ROADMAP_INDEX.md", md)
            db = _make_session()
            result = sync_roadmap(db, root)
        self.assertGreaterEqual(result.findings_created, 1)
        finding = (
            db.query(IntegrityFinding)
            .filter_by(finding_type="naming_violation", object_ref="BADID")
            .first()
        )
        self.assertIsNotNone(finding)
        self.assertEqual(finding.severity, "error")

    def test_valid_id_produces_no_naming_finding(self) -> None:
        md = "- `RM-CORE-001` — Good item\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "docs" / "roadmap" / "ROADMAP_INDEX.md", md)
            db = _make_session()
            sync_roadmap(db, root)
        count = (
            db.query(IntegrityFinding)
            .filter_by(finding_type="naming_violation")
            .count()
        )
        self.assertEqual(count, 0)

    def test_naming_violation_not_doubled_on_rerun(self) -> None:
        md = "- `BADID` — Missing prefix\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "docs" / "roadmap" / "ROADMAP_INDEX.md", md)
            db = _make_session()
            sync_roadmap(db, root)
            sync_roadmap(db, root)
        count = (
            db.query(IntegrityFinding)
            .filter_by(finding_type="naming_violation", object_ref="BADID")
            .count()
        )
        self.assertEqual(count, 1)


class DryRunTest(unittest.TestCase):
    def test_dry_run_does_not_write(self) -> None:
        md = "- `RM-GOV-002` — Dry run item\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "docs" / "roadmap" / "ROADMAP_INDEX.md", md)
            db = _make_session()
            result = sync_roadmap(db, root, dry_run=True)
        self.assertEqual(result.items_created, 1)
        self.assertEqual(db.query(RoadmapItem).count(), 0)
        self.assertEqual(db.query(IntegrityFinding).count(), 0)


class YamlOnlyItemTest(unittest.TestCase):
    def test_yaml_only_item_is_synced(self) -> None:
        """Items found only in docs/roadmap/items/*.yaml (not in markdown) are synced."""
        yaml_content = """\
schema_version: "1.0"
kind: "roadmap_item"
id: "RM-GOV-001"
title: "YAML-only item"
category: "GOV"
type: "platform_foundation"
status: "proposed"
priority: "P1"
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "docs" / "roadmap" / "ROADMAP_INDEX.md", "# No items\n")
            yaml_path = root / "docs" / "roadmap" / "items" / "RM-GOV-001.yaml"
            yaml_path.parent.mkdir(parents=True, exist_ok=True)
            yaml_path.write_text(yaml_content, encoding="utf-8")
            db = _make_session()
            result = sync_roadmap(db, root)
        self.assertEqual(result.items_created, 1)
        item = db.query(RoadmapItem).filter_by(id="RM-GOV-001").one()
        self.assertEqual(item.title, "YAML-only item")


if __name__ == "__main__":
    unittest.main()
