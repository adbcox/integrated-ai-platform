"""Tests for _read_after_retrieval_template() dynamic permission allowlist."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import bin.framework_control_plane as fcp


def _write_targets(tmp_dir: Path, targets: list[dict]) -> Path:
    p = tmp_dir / "retrieval_targets.json"
    p.write_text(json.dumps(targets), encoding="utf-8")
    return p


class TestReadAfterRetrievalPermissionBaseline(unittest.TestCase):
    def test_returns_dict(self):
        with tempfile.TemporaryDirectory() as td:
            result = fcp._read_after_retrieval_template(targets_path=Path(td) / "missing.json")
        self.assertIsInstance(result, dict)

    def test_permission_policy_key_present(self):
        with tempfile.TemporaryDirectory() as td:
            result = fcp._read_after_retrieval_template(targets_path=Path(td) / "missing.json")
        self.assertIn("permission_policy", result)

    def test_allow_edit_path_patterns_key_present(self):
        with tempfile.TemporaryDirectory() as td:
            result = fcp._read_after_retrieval_template(targets_path=Path(td) / "missing.json")
        self.assertIn("allow_edit_path_patterns", result["permission_policy"])

    def test_allow_edit_path_patterns_is_list(self):
        with tempfile.TemporaryDirectory() as td:
            result = fcp._read_after_retrieval_template(targets_path=Path(td) / "missing.json")
        self.assertIsInstance(result["permission_policy"]["allow_edit_path_patterns"], list)

    def test_output_artifact_always_in_patterns(self):
        with tempfile.TemporaryDirectory() as td:
            result = fcp._read_after_retrieval_template(targets_path=Path(td) / "missing.json")
        patterns = result["permission_policy"]["allow_edit_path_patterns"]
        self.assertTrue(
            any("read_after_retrieval_output" in p for p in patterns),
            f"Expected read_after_retrieval_output in patterns: {patterns}",
        )


class TestReadAfterRetrievalPermissionNoTargets(unittest.TestCase):
    def _result_no_targets(self) -> dict:
        with tempfile.TemporaryDirectory() as td:
            return fcp._read_after_retrieval_template(targets_path=Path(td) / "missing.json")

    def test_fallback_patterns_included_when_no_targets(self):
        patterns = self._result_no_targets()["permission_policy"]["allow_edit_path_patterns"]
        self.assertTrue(
            any("framework" in p for p in patterns),
            f"Expected framework fallback pattern: {patterns}",
        )

    def test_fallback_includes_bin_pattern(self):
        patterns = self._result_no_targets()["permission_policy"]["allow_edit_path_patterns"]
        self.assertTrue(any("bin" in p for p in patterns))

    def test_fallback_includes_tests_pattern(self):
        patterns = self._result_no_targets()["permission_policy"]["allow_edit_path_patterns"]
        self.assertTrue(any("tests" in p for p in patterns))

    def test_patterns_list_nonempty_when_no_targets(self):
        patterns = self._result_no_targets()["permission_policy"]["allow_edit_path_patterns"]
        self.assertGreater(len(patterns), 1)


class TestReadAfterRetrievalPermissionWithTargets(unittest.TestCase):
    def _targets(self) -> list[dict]:
        return [
            {"contract_name": "read_file", "arguments": {"path": "framework/worker_runtime.py"}},
            {"contract_name": "read_file", "arguments": {"path": "framework/job_schema.py"}},
        ]

    def _result_with_targets(self) -> dict:
        with tempfile.TemporaryDirectory() as td:
            p = _write_targets(Path(td), self._targets())
            return fcp._read_after_retrieval_template(targets_path=p)

    def test_target_paths_included_in_allow_patterns(self):
        import re as _re
        patterns = self._result_with_targets()["permission_policy"]["allow_edit_path_patterns"]
        target_paths = [t["arguments"]["path"] for t in self._targets()]
        for tp in target_paths:
            escaped = _re.escape(tp)
            self.assertTrue(
                any(escaped in p for p in patterns),
                f"Expected escaped path {escaped!r} in patterns: {patterns}",
            )

    def test_no_broad_fallback_when_targets_present(self):
        patterns = self._result_with_targets()["permission_policy"]["allow_edit_path_patterns"]
        self.assertFalse(
            any(p == r"^framework/" for p in patterns),
            f"Fallback pattern should not appear when targets loaded: {patterns}",
        )

    def test_output_artifact_still_present_with_targets(self):
        patterns = self._result_with_targets()["permission_policy"]["allow_edit_path_patterns"]
        self.assertTrue(any("read_after_retrieval_output" in p for p in patterns))

    def test_pattern_count_equals_targets_plus_one(self):
        patterns = self._result_with_targets()["permission_policy"]["allow_edit_path_patterns"]
        self.assertEqual(len(patterns), len(self._targets()) + 1)

    def test_patterns_are_strings(self):
        patterns = self._result_with_targets()["permission_policy"]["allow_edit_path_patterns"]
        for p in patterns:
            self.assertIsInstance(p, str)


class TestReadAfterRetrievalPermissionEdgeCases(unittest.TestCase):
    def test_empty_path_in_target_skipped(self):
        targets = [{"contract_name": "read_file", "arguments": {"path": ""}}]
        with tempfile.TemporaryDirectory() as td:
            p = _write_targets(Path(td), targets)
            result = fcp._read_after_retrieval_template(targets_path=p)
        patterns = result["permission_policy"]["allow_edit_path_patterns"]
        self.assertTrue(
            any("framework" in p2 for p2 in patterns),
            "Empty-path target should trigger fallback",
        )

    def test_missing_arguments_key_skipped(self):
        targets = [{"contract_name": "read_file"}]
        with tempfile.TemporaryDirectory() as td:
            p = _write_targets(Path(td), targets)
            result = fcp._read_after_retrieval_template(targets_path=p)
        patterns = result["permission_policy"]["allow_edit_path_patterns"]
        self.assertTrue(any("framework" in p2 for p2 in patterns))

    def test_none_path_in_arguments_skipped(self):
        targets = [{"contract_name": "read_file", "arguments": {"path": None}}]
        with tempfile.TemporaryDirectory() as td:
            p = _write_targets(Path(td), targets)
            result = fcp._read_after_retrieval_template(targets_path=p)
        patterns = result["permission_policy"]["allow_edit_path_patterns"]
        self.assertTrue(any("framework" in p2 for p2 in patterns))

    def test_phase2_typed_tools_includes_read_specs(self):
        targets = [{"contract_name": "read_file", "arguments": {"path": "framework/worker_runtime.py"}}]
        with tempfile.TemporaryDirectory() as td:
            p = _write_targets(Path(td), targets)
            result = fcp._read_after_retrieval_template(targets_path=p)
        tools = result["phase2_typed_tools"]
        read_tools = [t for t in tools if t.get("contract_name") == "read_file"]
        self.assertGreater(len(read_tools), 0)

    def test_phase2_typed_tools_includes_apply_patch_sentinel(self):
        with tempfile.TemporaryDirectory() as td:
            result = fcp._read_after_retrieval_template(targets_path=Path(td) / "missing.json")
        tools = result["phase2_typed_tools"]
        patch_tools = [t for t in tools if t.get("contract_name") == "apply_patch"]
        self.assertEqual(len(patch_tools), 1)


if __name__ == "__main__":
    unittest.main()
