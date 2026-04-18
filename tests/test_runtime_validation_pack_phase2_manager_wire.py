"""Tests for runtime_validation_pack Phase 2 manager-wire helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from framework.runtime_validation_pack import (
    assert_phase2_manager_wire_present,
    run_phase2_manager_wire_validation,
)


class TestRunPhase2ManagerWireValidation(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="p2_mgr_wire_pack_")
        self._tmp_path = Path(self._tmp)

    def _run(self):
        return run_phase2_manager_wire_validation(base_root=self._tmp_path)

    def test_returns_runtime_payload_and_manager_view(self):
        result = self._run()
        self.assertIn("runtime_payload", result)
        self.assertIn("manager_view", result)

    def test_assert_present_returns_empty_list(self):
        result = self._run()
        errors = assert_phase2_manager_wire_present(result)
        self.assertEqual(errors, [], f"Unexpected errors: {errors}")

    def test_manager_view_phase2_payload_present_true(self):
        result = self._run()
        view = result["manager_view"]
        self.assertTrue(view.get("phase2_payload_present"), f"view={view}")

    def test_typed_tool_summary_tool_count_ge_1(self):
        result = self._run()
        tool_summary = result["manager_view"].get("typed_tool_summary") or {}
        self.assertGreaterEqual(
            tool_summary.get("tool_count", 0), 1,
            f"tool_summary={tool_summary}",
        )


if __name__ == "__main__":
    unittest.main()
