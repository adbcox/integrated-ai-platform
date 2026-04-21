"""Offline tests for canonical validation artifact emitter (EXEC-EVIDENCE-A1-VALID-SEAM-2).

Covers:
- emit produces one parseable JSONL line
- emit appends, not overwrites
- latest.json reflects most recent record
- record_id starts with val-
- supported outcomes emit cleanly
- dry_run writes nothing
- checks serialize correctly
- spec parses and covers required fields
- emitter surfaces OSError with context on bad path
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.validation_artifact_writer import (
    ValidationCheck,
    ValidationRecord,
    emit_validation_record,
)

SPEC_PATH = REPO_ROOT / "governance" / "validation_artifact_spec.json"


def _make_record(**kwargs) -> ValidationRecord:
    defaults = dict(
        emitter="tests/test_validation_artifact_seam.py",
        validation_type="unit_test",
        outcome="pass",
    )
    defaults.update(kwargs)
    return ValidationRecord(**defaults)


class EmitBasicTest(unittest.TestCase):
    """emit_validation_record writes one parseable JSONL line."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.artifact_dir = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_emit_creates_records_jsonl(self) -> None:
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        self.assertTrue((self.artifact_dir / "records.jsonl").exists())

    def test_emit_creates_latest_json(self) -> None:
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        self.assertTrue((self.artifact_dir / "latest.json").exists())

    def test_emit_returns_jsonl_path(self) -> None:
        result = emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith("records.jsonl"))

    def test_jsonl_line_is_parseable(self) -> None:
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        self.assertIsInstance(parsed, dict)

    def test_record_id_starts_with_val_dash(self) -> None:
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        self.assertTrue(parsed["record_id"].startswith("val-"), parsed["record_id"])

    def test_record_id_format_val_8hex(self) -> None:
        import re
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        self.assertRegex(parsed["record_id"], r"^val-[0-9a-f]{8}$")

    def test_schema_version_is_1_0_0(self) -> None:
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        self.assertEqual(parsed["schema_version"], "1.0.0")

    def test_emitter_field_preserved(self) -> None:
        emit_validation_record(
            _make_record(emitter="bin/run_baseline_validation.py"),
            artifact_dir=self.artifact_dir,
        )
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        self.assertEqual(parsed["emitter"], "bin/run_baseline_validation.py")

    def test_outcome_field_preserved(self) -> None:
        emit_validation_record(_make_record(outcome="fail"), artifact_dir=self.artifact_dir)
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        self.assertEqual(parsed["outcome"], "fail")

    def test_emitted_at_is_iso_utc(self) -> None:
        import re
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        self.assertRegex(parsed["emitted_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$")


class AppendBehaviorTest(unittest.TestCase):
    """emit appends to records.jsonl, does not overwrite."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.artifact_dir = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_second_emit_appends_second_line(self) -> None:
        emit_validation_record(_make_record(outcome="pass"), artifact_dir=self.artifact_dir)
        emit_validation_record(_make_record(outcome="fail"), artifact_dir=self.artifact_dir)
        lines = (self.artifact_dir / "records.jsonl").read_text().strip().splitlines()
        self.assertEqual(len(lines), 2)

    def test_both_lines_are_parseable(self) -> None:
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        lines = (self.artifact_dir / "records.jsonl").read_text().strip().splitlines()
        for line in lines:
            self.assertIsInstance(json.loads(line), dict)

    def test_record_ids_are_distinct(self) -> None:
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        lines = (self.artifact_dir / "records.jsonl").read_text().strip().splitlines()
        ids = [json.loads(l)["record_id"] for l in lines]
        self.assertEqual(len(ids), len(set(ids)))

    def test_latest_json_reflects_most_recent(self) -> None:
        emit_validation_record(_make_record(outcome="pass"), artifact_dir=self.artifact_dir)
        emit_validation_record(_make_record(outcome="fail"), artifact_dir=self.artifact_dir)
        latest = json.loads((self.artifact_dir / "latest.json").read_text())
        self.assertEqual(latest["outcome"], "fail")

    def test_latest_json_record_id_matches_last_jsonl_line(self) -> None:
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        lines = (self.artifact_dir / "records.jsonl").read_text().strip().splitlines()
        last_id = json.loads(lines[-1])["record_id"]
        latest_id = json.loads((self.artifact_dir / "latest.json").read_text())["record_id"]
        self.assertEqual(last_id, latest_id)


class OutcomeVariantsTest(unittest.TestCase):
    """All four spec outcomes emit cleanly."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.artifact_dir = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _emit_outcome(self, outcome: str) -> dict:
        emit_validation_record(_make_record(outcome=outcome), artifact_dir=self.artifact_dir)
        lines = (self.artifact_dir / "records.jsonl").read_text().strip().splitlines()
        return json.loads(lines[-1])

    def test_outcome_pass(self) -> None:
        parsed = self._emit_outcome("pass")
        self.assertEqual(parsed["outcome"], "pass")

    def test_outcome_fail(self) -> None:
        parsed = self._emit_outcome("fail")
        self.assertEqual(parsed["outcome"], "fail")

    def test_outcome_skip(self) -> None:
        parsed = self._emit_outcome("skip")
        self.assertEqual(parsed["outcome"], "skip")

    def test_outcome_error(self) -> None:
        parsed = self._emit_outcome("error")
        self.assertEqual(parsed["outcome"], "error")


class DryRunTest(unittest.TestCase):
    """dry_run=True writes nothing and returns None."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.artifact_dir = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_dry_run_returns_none(self) -> None:
        result = emit_validation_record(_make_record(), artifact_dir=self.artifact_dir, dry_run=True)
        self.assertIsNone(result)

    def test_dry_run_no_files_written(self) -> None:
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir, dry_run=True)
        self.assertFalse((self.artifact_dir / "records.jsonl").exists())
        self.assertFalse((self.artifact_dir / "latest.json").exists())

    def test_dry_run_does_not_affect_subsequent_real_emit(self) -> None:
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir, dry_run=True)
        emit_validation_record(_make_record(outcome="pass"), artifact_dir=self.artifact_dir)
        lines = (self.artifact_dir / "records.jsonl").read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)


class ChecksSerializationTest(unittest.TestCase):
    """Checks field serializes correctly."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.artifact_dir = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_checks_list_present_in_output(self) -> None:
        record = ValidationRecord(
            emitter="test",
            validation_type="unit_test",
            outcome="pass",
            checks=(
                ValidationCheck(check_name="alpha", outcome="pass", detail="ok"),
                ValidationCheck(check_name="beta", outcome="fail", detail="rc=1"),
            ),
        )
        emit_validation_record(record, artifact_dir=self.artifact_dir)
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        self.assertIsInstance(parsed["checks"], list)
        self.assertEqual(len(parsed["checks"]), 2)

    def test_check_names_preserved(self) -> None:
        record = ValidationRecord(
            emitter="test",
            validation_type="unit_test",
            outcome="pass",
            checks=(
                ValidationCheck(check_name="check", outcome="pass"),
                ValidationCheck(check_name="quick", outcome="pass"),
            ),
        )
        emit_validation_record(record, artifact_dir=self.artifact_dir)
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        names = [c["check_name"] for c in parsed["checks"]]
        self.assertIn("check", names)
        self.assertIn("quick", names)

    def test_check_detail_none_when_not_provided(self) -> None:
        record = ValidationRecord(
            emitter="test",
            validation_type="unit_test",
            outcome="pass",
            checks=(ValidationCheck(check_name="alpha", outcome="pass"),),
        )
        emit_validation_record(record, artifact_dir=self.artifact_dir)
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        self.assertIsNone(parsed["checks"][0]["detail"])

    def test_empty_checks_is_empty_list(self) -> None:
        emit_validation_record(_make_record(), artifact_dir=self.artifact_dir)
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        self.assertEqual(parsed["checks"], [])

    def test_artifact_refs_serialized(self) -> None:
        record = ValidationRecord(
            emitter="test",
            validation_type="unit_test",
            outcome="pass",
            artifact_refs=("artifacts/baseline_validation/latest.json",),
        )
        emit_validation_record(record, artifact_dir=self.artifact_dir)
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        self.assertIn("artifacts/baseline_validation/latest.json", parsed["artifact_refs"])

    def test_notes_preserved(self) -> None:
        record = ValidationRecord(
            emitter="test",
            validation_type="unit_test",
            outcome="pass",
            notes="baseline_commit=abc123",
        )
        emit_validation_record(record, artifact_dir=self.artifact_dir)
        line = (self.artifact_dir / "records.jsonl").read_text().strip()
        parsed = json.loads(line)
        self.assertEqual(parsed["notes"], "baseline_commit=abc123")


class ErrorHandlingTest(unittest.TestCase):
    """OSError surfaced with context on bad path."""

    def test_bad_artifact_dir_raises_oserror(self) -> None:
        bad_path = Path("/proc/nonexistent_readonly_path/deep/subdir")
        with self.assertRaises(OSError) as ctx:
            emit_validation_record(_make_record(), artifact_dir=bad_path)
        self.assertIn("validation_artifact_writer", str(ctx.exception))


class SpecFileTest(unittest.TestCase):
    """governance/validation_artifact_spec.json parses and covers required fields."""

    def setUp(self) -> None:
        self.spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    def test_spec_parses(self) -> None:
        self.assertIsInstance(self.spec, dict)

    def test_spec_has_schema_version(self) -> None:
        self.assertIn("schema_version", self.spec)
        self.assertEqual(self.spec["schema_version"], "1.0.0")

    def test_spec_has_authority_owner(self) -> None:
        self.assertIn("authority_owner", self.spec)

    def test_spec_has_record_format(self) -> None:
        self.assertIn("record_format", self.spec)

    def test_spec_has_output_policy(self) -> None:
        self.assertIn("output_policy", self.spec)

    def test_record_format_covers_required_fields(self) -> None:
        required = {"record_id", "schema_version", "emitted_at", "emitter",
                    "validation_type", "outcome", "checks", "artifact_refs"}
        covered = set(self.spec["record_format"].keys())
        missing = required - covered
        self.assertEqual(missing, set(), f"spec missing fields: {missing}")

    def test_outcome_enum_includes_four_values(self) -> None:
        outcome_spec = self.spec["record_format"]["outcome"]
        self.assertIn("enum", outcome_spec)
        enum_vals = set(outcome_spec["enum"])
        self.assertGreaterEqual(enum_vals, {"pass", "fail", "skip", "error"})

    def test_output_policy_mentions_append(self) -> None:
        policy = self.spec["output_policy"]
        records_policy = policy.get("records_jsonl", "")
        self.assertIn("append", records_policy.lower())

    def test_output_location_present(self) -> None:
        self.assertIn("output_location", self.spec)
        loc = self.spec["output_location"]
        self.assertIn("records_jsonl", loc)
        self.assertIn("latest_json", loc)


if __name__ == "__main__":
    unittest.main()
