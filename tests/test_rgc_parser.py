"""Offline tests for roadmap_governance/parser.py.

Tests cover: markdown parsing, YAML enrichment, naming validation,
and domain extraction.  All tests use tempfile for isolation.
"""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from roadmap_governance.parser import (
    parse_index_md,
    scan_item_yamls,
    validate_naming,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


_MINIMAL_YAML = """\
schema_version: "1.0"
kind: "roadmap_item"
id: "{id}"
title: "{title}"
category: "{category}"
type: "governance"
status: "proposed"
priority: "P1"
description: "A test description."
"""


class NamingValidationTest(unittest.TestCase):
    def test_valid_simple(self) -> None:
        self.assertTrue(validate_naming("RM-GOV-001"))

    def test_valid_core(self) -> None:
        self.assertTrue(validate_naming("RM-CORE-006"))

    def test_valid_compound_domain(self) -> None:
        self.assertTrue(validate_naming("RM-AUTO-MECH-001"))

    def test_valid_long_number(self) -> None:
        self.assertTrue(validate_naming("RM-OPS-1234"))

    def test_invalid_no_prefix(self) -> None:
        self.assertFalse(validate_naming("GOV-001"))

    def test_invalid_lowercase(self) -> None:
        self.assertFalse(validate_naming("rm-gov-001"))

    def test_invalid_short_number(self) -> None:
        self.assertFalse(validate_naming("RM-GOV-01"))

    def test_invalid_no_number(self) -> None:
        self.assertFalse(validate_naming("RM-GOV"))

    def test_invalid_empty(self) -> None:
        self.assertFalse(validate_naming(""))

    def test_invalid_number_in_domain(self) -> None:
        # Domain segment starting with digit is invalid
        self.assertFalse(validate_naming("RM-1GOV-001"))


class ParseIndexMdTest(unittest.TestCase):
    def test_empty_file_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "docs" / "roadmap" / "ROADMAP_INDEX.md"
            _write(index, "# Roadmap\n\nNo items yet.\n")
            result = parse_index_md(index, root)
        self.assertEqual(result, [])

    def test_missing_file_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "docs" / "roadmap" / "ROADMAP_INDEX.md"
            result = parse_index_md(index, root)
        self.assertEqual(result, [])

    def test_parses_em_dash_items(self) -> None:
        md = """\
            ## Items

            - `RM-GOV-002` — Reconcile source-of-truth
            - `RM-GOV-003` — Create core ADR set
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "docs" / "roadmap" / "ROADMAP_INDEX.md"
            _write(index, md)
            items = parse_index_md(index, root)
        self.assertEqual(len(items), 2)
        ids = [i.id for i in items]
        self.assertIn("RM-GOV-002", ids)
        self.assertIn("RM-GOV-003", ids)

    def test_title_from_markdown_when_no_yaml(self) -> None:
        md = "- `RM-GOV-099` — Some custom title\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "docs" / "roadmap" / "ROADMAP_INDEX.md"
            _write(index, md)
            items = parse_index_md(index, root)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Some custom title")
        self.assertEqual(items[0].category, "GOV")
        self.assertFalse(items[0].from_yaml)

    def test_enriched_from_yaml(self) -> None:
        md = "- `RM-GOV-001` — Override title\n"
        yaml_content = _MINIMAL_YAML.format(
            id="RM-GOV-001",
            title="Canonical YAML title",
            category="GOV",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "docs" / "roadmap" / "ROADMAP_INDEX.md"
            yaml_file = root / "docs" / "roadmap" / "items" / "RM-GOV-001.yaml"
            _write(index, md)
            _write(yaml_file, yaml_content)
            items = parse_index_md(index, root)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item.title, "Canonical YAML title")
        self.assertEqual(item.status, "proposed")
        self.assertEqual(item.priority, "P1")
        self.assertEqual(item.item_type, "governance")
        self.assertEqual(item.description, "A test description.")
        self.assertTrue(item.from_yaml)

    def test_source_hash_is_stable(self) -> None:
        md = "- `RM-GOV-002` — Reconcile source-of-truth\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "docs" / "roadmap" / "ROADMAP_INDEX.md"
            _write(index, md)
            items1 = parse_index_md(index, root)
            items2 = parse_index_md(index, root)
        self.assertEqual(items1[0].source_hash, items2[0].source_hash)

    def test_duplicate_ids_both_returned(self) -> None:
        md = (
            "- `RM-GOV-002` — First occurrence\n"
            "- `RM-GOV-002` — Second occurrence\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index = root / "docs" / "roadmap" / "ROADMAP_INDEX.md"
            _write(index, md)
            items = parse_index_md(index, root)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].id, "RM-GOV-002")
        self.assertEqual(items[1].id, "RM-GOV-002")


class ScanItemYamlsTest(unittest.TestCase):
    def test_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "roadmap" / "items").mkdir(parents=True)
            result = scan_item_yamls(root)
        self.assertEqual(result, [])

    def test_missing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = scan_item_yamls(Path(tmp))
        self.assertEqual(result, [])

    def test_discovers_yaml_items(self) -> None:
        yaml1 = _MINIMAL_YAML.format(id="RM-GOV-001", title="T1", category="GOV")
        yaml2 = _MINIMAL_YAML.format(id="RM-CORE-001", title="T2", category="CORE")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            items_dir = root / "docs" / "roadmap" / "items"
            items_dir.mkdir(parents=True)
            (items_dir / "RM-GOV-001.yaml").write_text(yaml1, encoding="utf-8")
            (items_dir / "RM-CORE-001.yaml").write_text(yaml2, encoding="utf-8")
            items = scan_item_yamls(root)
        ids = {i.id for i in items}
        self.assertIn("RM-GOV-001", ids)
        self.assertIn("RM-CORE-001", ids)

    def test_yaml_without_id_is_skipped(self) -> None:
        bad_yaml = "title: 'No ID here'\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            items_dir = root / "docs" / "roadmap" / "items"
            items_dir.mkdir(parents=True)
            (items_dir / "bad.yaml").write_text(bad_yaml, encoding="utf-8")
            items = scan_item_yamls(root)
        self.assertEqual(items, [])


if __name__ == "__main__":
    unittest.main()
