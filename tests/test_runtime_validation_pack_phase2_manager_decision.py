"""Tests for runtime_validation_pack Phase 2 manager-decision helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from framework.runtime_validation_pack import (
    assert_phase2_manager_decision_present,
    run_phase2_manager_decision_validation,
)

_VALID_SIGNALS = frozenset(
    {"ok", "all_tools_blocked", "no_tools_ran", "partial_block", "phase2_absent"}
)


class TestRunPhase2ManagerDecisionValidation(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="p2_mgr_decision_pack_")
        self._tmp_path = Path(self._tmp)

    def _run(self):
        return run_phase2_manager_decision_validation(base_root=self._tmp_path)

    def test_returns_runtime_payload_manager_view_operational_signal(self):
        result = self._run()
        self.assertIn("runtime_payload", result)
        self.assertIn("manager_view", result)
        self.assertIn("operational_signal", result)

    def test_assert_present_returns_empty_list(self):
        result = self._run()
        errors = assert_phase2_manager_decision_present(result)
        self.assertEqual(errors, [], f"Unexpected errors: {errors}")

    def test_operational_signal_is_valid_value(self):
        result = self._run()
        sig = result["operational_signal"].get("signal")
        self.assertIn(sig, _VALID_SIGNALS, f"signal={sig!r}")

    def test_blocked_and_executed_counts_are_int(self):
        result = self._run()
        sig = result["operational_signal"]
        self.assertIsInstance(sig.get("blocked_count"), int)
        self.assertIsInstance(sig.get("executed_count"), int)


if __name__ == "__main__":
    unittest.main()
