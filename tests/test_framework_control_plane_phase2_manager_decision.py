"""Tests for _phase2_manager_decision in framework_control_plane."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from framework.framework_control_plane import _phase2_manager_decision

_VALID_SIGNALS = frozenset(
    {"ok", "all_tools_blocked", "no_tools_ran", "partial_block", "phase2_absent"}
)


def _view(*, present=True, tool_count=3, blocked_count=0, executed_count=3, final_outcome="completed"):
    if not present:
        return {"phase2_payload_present": False, "final_outcome": final_outcome}
    return {
        "phase2_payload_present": True,
        "typed_tool_summary": {
            "tool_count": tool_count,
            "blocked_count": blocked_count,
            "executed_count": executed_count,
        },
        "final_outcome": final_outcome,
    }


class TestPhase2ManagerDecisionSignals(unittest.TestCase):
    def test_phase2_absent_when_payload_not_present(self):
        result = _phase2_manager_decision(_view(present=False))
        self.assertEqual(result["signal"], "phase2_absent")

    def test_no_tools_ran_when_tool_count_zero(self):
        result = _phase2_manager_decision(_view(tool_count=0, blocked_count=0, executed_count=0))
        self.assertEqual(result["signal"], "no_tools_ran")

    def test_all_tools_blocked_when_blocked_gt_0_and_executed_eq_0(self):
        result = _phase2_manager_decision(_view(tool_count=2, blocked_count=2, executed_count=0))
        self.assertEqual(result["signal"], "all_tools_blocked")

    def test_partial_block_when_blocked_gt_0_and_executed_gt_0(self):
        result = _phase2_manager_decision(_view(tool_count=3, blocked_count=1, executed_count=2))
        self.assertEqual(result["signal"], "partial_block")

    def test_ok_when_no_blocks_and_executed_gt_0(self):
        result = _phase2_manager_decision(_view(tool_count=3, blocked_count=0, executed_count=3))
        self.assertEqual(result["signal"], "ok")

    def test_final_outcome_echoed_from_manager_view(self):
        result = _phase2_manager_decision(_view(final_outcome="completed"))
        self.assertEqual(result["final_outcome"], "completed")

    def test_all_five_valid_signals_are_distinct_and_correct(self):
        signals = {
            _phase2_manager_decision(_view(present=False))["signal"],
            _phase2_manager_decision(_view(tool_count=0, blocked_count=0, executed_count=0))["signal"],
            _phase2_manager_decision(_view(tool_count=2, blocked_count=2, executed_count=0))["signal"],
            _phase2_manager_decision(_view(tool_count=3, blocked_count=1, executed_count=2))["signal"],
            _phase2_manager_decision(_view(tool_count=3, blocked_count=0, executed_count=3))["signal"],
        }
        self.assertEqual(signals, _VALID_SIGNALS)


if __name__ == "__main__":
    unittest.main()
