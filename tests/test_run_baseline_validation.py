"""Offline tests for bin/run_baseline_validation.py.

All tests use dry_run=True, write_artifact=False so no real make targets
are invoked and no files are written.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bin"))


def _dry_run():
    from run_baseline_validation import run_baseline_validation
    return run_baseline_validation(dry_run=True, write_artifact=False)


class BaselineValidationSchemaTest(unittest.TestCase):
    def setUp(self):
        self.result = _dry_run()

    def test_result_is_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_schema_version_is_1(self):
        self.assertEqual(self.result["schema_version"], 1)

    def test_required_top_level_keys_exist(self):
        required = [
            "schema_version",
            "generated_at",
            "baseline_commit",
            "definition_of_done_ref",
            "dry_run",
            "commands",
            "all_passed",
            "definition_of_done_met",
        ]
        for key in required:
            self.assertIn(key, self.result, msg=f"missing key {key!r}")

    def test_dry_run_is_true(self):
        self.assertTrue(self.result["dry_run"])

    def test_definition_of_done_ref_matches_constant(self):
        from run_baseline_validation import DEFINITION_OF_DONE_REF
        self.assertEqual(self.result["definition_of_done_ref"], DEFINITION_OF_DONE_REF)

    def test_all_passed_is_true_in_dry_run(self):
        self.assertTrue(self.result["all_passed"])

    def test_definition_of_done_met_is_true_in_dry_run(self):
        self.assertTrue(self.result["definition_of_done_met"])


class BaselineCommandEntriesTest(unittest.TestCase):
    def setUp(self):
        self.result = _dry_run()
        self.commands = self.result["commands"]

    def test_check_present(self):
        self.assertIn("check", self.commands)

    def test_quick_present(self):
        self.assertIn("quick", self.commands)

    def test_each_command_entry_has_required_fields(self):
        required_fields = [
            "command_name",
            "argv",
            "return_code",
            "success",
            "duration_ms",
            "stdout_head",
            "stderr_head",
            "started_at",
            "completed_at",
        ]
        for cmd_name, entry in self.commands.items():
            for field in required_fields:
                self.assertIn(field, entry, msg=f"command {cmd_name!r} missing field {field!r}")

    def test_dry_run_success_true_for_check(self):
        self.assertTrue(self.commands["check"]["success"])

    def test_dry_run_success_true_for_quick(self):
        self.assertTrue(self.commands["quick"]["success"])

    def test_dry_run_stdout_contains_dry_run_marker(self):
        for cmd_name, entry in self.commands.items():
            self.assertIn("[dry-run]", entry["stdout_head"], msg=f"{cmd_name} missing [dry-run] marker")


class BaselineArtifactWriteTest(unittest.TestCase):
    def test_artifact_file_is_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "latest.json"
            import run_baseline_validation as m
            with mock.patch.object(m, "BASELINE_LATEST", artifact_path), \
                 mock.patch.object(m, "BASELINE_ARTIFACT_ROOT", Path(tmpdir)):
                m.run_baseline_validation(dry_run=True, write_artifact=True)
            self.assertTrue(artifact_path.exists())

    def test_written_file_parses_as_json_with_all_passed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = Path(tmpdir) / "latest.json"
            import run_baseline_validation as m
            with mock.patch.object(m, "BASELINE_LATEST", artifact_path), \
                 mock.patch.object(m, "BASELINE_ARTIFACT_ROOT", Path(tmpdir)):
                m.run_baseline_validation(dry_run=True, write_artifact=True)
            data = json.loads(artifact_path.read_text())
            self.assertIn("all_passed", data)
            self.assertTrue(data["all_passed"])


if __name__ == "__main__":
    unittest.main()
