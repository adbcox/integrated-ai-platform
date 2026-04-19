"""Tests for _compute_phase3_continuation_exit_code in bin/framework_control_plane.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bin.framework_control_plane import _compute_phase3_continuation_exit_code


def _cont_output(ran: bool, action: str | None = None) -> dict:
    cont: dict = {"ran": ran}
    if action is not None:
        cont["phase3_continuation_next_action"] = {"action": action}
    return {"phase3_continuation_result": cont}


class TestComputePhase3ContinuationExitCode(unittest.TestCase):
    def test_returns_minus_one_for_empty_output(self):
        self.assertEqual(_compute_phase3_continuation_exit_code({}), -1)

    def test_returns_minus_one_when_continuation_result_absent(self):
        self.assertEqual(_compute_phase3_continuation_exit_code({"other": "value"}), -1)

    def test_returns_minus_one_when_ran_false(self):
        self.assertEqual(_compute_phase3_continuation_exit_code(_cont_output(ran=False, action="ready")), -1)

    def test_returns_minus_one_when_continuation_result_not_dict(self):
        self.assertEqual(_compute_phase3_continuation_exit_code({"phase3_continuation_result": "bad"}), -1)

    def test_returns_zero_when_ran_true_and_action_ready(self):
        self.assertEqual(_compute_phase3_continuation_exit_code(_cont_output(ran=True, action="ready")), 0)

    def test_returns_five_when_ran_true_and_action_refine_retrieval(self):
        self.assertEqual(_compute_phase3_continuation_exit_code(_cont_output(ran=True, action="refine_retrieval")), 5)

    def test_returns_six_when_ran_true_and_action_insufficient_context(self):
        self.assertEqual(_compute_phase3_continuation_exit_code(_cont_output(ran=True, action="insufficient_context")), 6)

    def test_returns_zero_when_ran_true_and_action_unknown(self):
        self.assertEqual(_compute_phase3_continuation_exit_code(_cont_output(ran=True, action="some_unknown_action")), 0)

    def test_returns_zero_when_ran_true_and_next_action_missing(self):
        self.assertEqual(_compute_phase3_continuation_exit_code({"phase3_continuation_result": {"ran": True}}), 0)


class TestContinuationExitOverrideIntegration(unittest.TestCase):
    def _apply_override(self, primary_exit: int, cont_exit: int) -> int:
        if cont_exit >= 0:
            return cont_exit
        return primary_exit

    def test_primary_refine_retrieval_continuation_ready_yields_zero(self):
        output = {
            "phase3_next_action": {"action": "refine_retrieval"},
            "phase3_continuation_result": {
                "ran": True,
                "phase3_continuation_next_action": {"action": "ready"},
            },
        }
        cont_exit = _compute_phase3_continuation_exit_code(output)
        self.assertEqual(cont_exit, 0)
        final = self._apply_override(primary_exit=5, cont_exit=cont_exit)
        self.assertEqual(final, 0)

    def test_primary_refine_retrieval_continuation_still_refine_yields_five(self):
        output = {
            "phase3_next_action": {"action": "refine_retrieval"},
            "phase3_continuation_result": {
                "ran": True,
                "phase3_continuation_next_action": {"action": "refine_retrieval"},
            },
        }
        cont_exit = _compute_phase3_continuation_exit_code(output)
        self.assertEqual(cont_exit, 5)
        final = self._apply_override(primary_exit=5, cont_exit=cont_exit)
        self.assertEqual(final, 5)

    def test_no_continuation_primary_exit_unchanged(self):
        output = {"phase3_next_action": {"action": "refine_retrieval"}}
        cont_exit = _compute_phase3_continuation_exit_code(output)
        self.assertEqual(cont_exit, -1)
        final = self._apply_override(primary_exit=5, cont_exit=cont_exit)
        self.assertEqual(final, 5)


class TestSourceTextAssertions(unittest.TestCase):
    def _source(self):
        return (Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py").read_text()

    def test_compute_phase3_continuation_exit_code_in_source(self):
        self.assertIn("_compute_phase3_continuation_exit_code", self._source())

    def test_phase3_continuation_ran_true_in_source(self):
        self.assertIn("phase3_continuation_ran=true", self._source())


if __name__ == "__main__":
    unittest.main()
