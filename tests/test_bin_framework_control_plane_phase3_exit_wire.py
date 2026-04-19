"""Tests for _compute_phase3_exit_code in bin/framework_control_plane.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bin.framework_control_plane import _compute_phase2_exit_code, _compute_phase3_exit_code


def _idle_terminal_output(action: str | None = None) -> dict:
    out: dict = {
        "idle_reached": True,
        "phase2_operational_signal": {"signal": "ok"},
    }
    if action is not None:
        out["phase3_next_action"] = {"action": action}
    return out


def _terminal_rows() -> list:
    return [{"result": {"status": "completed"}}]


class TestComputePhase3ExitCodeDirect(unittest.TestCase):
    def test_empty_output_returns_zero(self):
        self.assertEqual(_compute_phase3_exit_code({}), 0)

    def test_empty_next_action_dict_returns_zero(self):
        self.assertEqual(_compute_phase3_exit_code({"phase3_next_action": {}}), 0)

    def test_ready_returns_zero(self):
        self.assertEqual(_compute_phase3_exit_code({"phase3_next_action": {"action": "ready"}}), 0)

    def test_no_context_returns_zero(self):
        self.assertEqual(_compute_phase3_exit_code({"phase3_next_action": {"action": "no_context"}}), 0)

    def test_refine_retrieval_returns_five(self):
        self.assertEqual(_compute_phase3_exit_code({"phase3_next_action": {"action": "refine_retrieval"}}), 5)

    def test_insufficient_context_returns_six(self):
        self.assertEqual(_compute_phase3_exit_code({"phase3_next_action": {"action": "insufficient_context"}}), 6)

    def test_uppercase_action_returns_zero(self):
        self.assertEqual(_compute_phase3_exit_code({"phase3_next_action": {"action": "REFINE_RETRIEVAL"}}), 0)

    def test_none_next_action_returns_zero(self):
        self.assertEqual(_compute_phase3_exit_code({"phase3_next_action": None}), 0)

    def test_string_next_action_returns_zero(self):
        self.assertEqual(_compute_phase3_exit_code({"phase3_next_action": "bad"}), 0)


class TestPhase2Phase3ExitInteraction(unittest.TestCase):
    def test_phase2_idle_false_returns_two_phase3_not_applied(self):
        output = {"idle_reached": False, "phase3_next_action": {"action": "refine_retrieval"}}
        p2 = _compute_phase2_exit_code(output, _terminal_rows())
        self.assertEqual(p2, 2)

    def test_phase2_zero_phase3_ready_returns_zero(self):
        output = _idle_terminal_output("ready")
        p2 = _compute_phase2_exit_code(output, _terminal_rows())
        self.assertEqual(p2, 0)
        final = p2 if p2 != 0 else _compute_phase3_exit_code(output)
        self.assertEqual(final, 0)

    def test_phase2_zero_phase3_refine_returns_five(self):
        output = _idle_terminal_output("refine_retrieval")
        p2 = _compute_phase2_exit_code(output, _terminal_rows())
        self.assertEqual(p2, 0)
        final = p2 if p2 != 0 else _compute_phase3_exit_code(output)
        self.assertEqual(final, 5)

    def test_phase2_zero_phase3_insufficient_returns_six(self):
        output = _idle_terminal_output("insufficient_context")
        p2 = _compute_phase2_exit_code(output, _terminal_rows())
        self.assertEqual(p2, 0)
        final = p2 if p2 != 0 else _compute_phase3_exit_code(output)
        self.assertEqual(final, 6)

    def test_phase2_four_phase3_refine_stays_four(self):
        output = {
            "idle_reached": True,
            "phase2_operational_signal": {"signal": "all_tools_blocked"},
            "phase3_next_action": {"action": "refine_retrieval"},
        }
        p2 = _compute_phase2_exit_code(output, _terminal_rows())
        self.assertEqual(p2, 4)
        final = p2 if p2 != 0 else _compute_phase3_exit_code(output)
        self.assertEqual(final, 4)

    def test_importable_from_bin(self):
        from bin.framework_control_plane import _compute_phase3_exit_code as fn
        self.assertTrue(callable(fn))


if __name__ == "__main__":
    unittest.main()
