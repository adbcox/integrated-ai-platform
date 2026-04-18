"""Tests for _compute_phase2_exit_code in bin/framework_control_plane.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bin.framework_control_plane import _compute_phase2_exit_code


def _make_output(*, idle_reached: bool, signal: str) -> dict:
    return {
        "idle_reached": idle_reached,
        "phase2_operational_signal": {"signal": signal},
    }


def _terminal_rows() -> list[dict]:
    return [{"result": {"status": "completed"}}]


def _non_terminal_rows() -> list[dict]:
    return [{"result": {"status": "pending"}}]


class TestExitCode2NotIdle(unittest.TestCase):
    def test_not_idle_returns_2(self):
        output = _make_output(idle_reached=False, signal="ok")
        self.assertEqual(_compute_phase2_exit_code(output, _terminal_rows()), 2)

    def test_not_idle_takes_precedence_over_blocked_signal(self):
        output = _make_output(idle_reached=False, signal="all_tools_blocked")
        self.assertEqual(_compute_phase2_exit_code(output, _terminal_rows()), 2)


class TestExitCode3NonTerminal(unittest.TestCase):
    def test_idle_non_terminal_returns_3(self):
        output = _make_output(idle_reached=True, signal="ok")
        self.assertEqual(_compute_phase2_exit_code(output, _non_terminal_rows()), 3)

    def test_idle_empty_result_rows_returns_3(self):
        output = _make_output(idle_reached=True, signal="ok")
        self.assertEqual(_compute_phase2_exit_code(output, []), 3)

    def test_idle_mixed_statuses_returns_3(self):
        rows = [{"result": {"status": "completed"}}, {"result": {"status": "pending"}}]
        output = _make_output(idle_reached=True, signal="ok")
        self.assertEqual(_compute_phase2_exit_code(output, rows), 3)


class TestExitCode4AllToolsBlocked(unittest.TestCase):
    def test_all_tools_blocked_signal_returns_4(self):
        output = _make_output(idle_reached=True, signal="all_tools_blocked")
        self.assertEqual(_compute_phase2_exit_code(output, _terminal_rows()), 4)

    def test_escalated_terminal_with_all_tools_blocked_returns_4(self):
        rows = [{"result": {"status": "escalated"}}]
        output = _make_output(idle_reached=True, signal="all_tools_blocked")
        self.assertEqual(_compute_phase2_exit_code(output, rows), 4)


class TestExitCode0Success(unittest.TestCase):
    def test_idle_terminal_ok_signal_returns_0(self):
        output = _make_output(idle_reached=True, signal="ok")
        self.assertEqual(_compute_phase2_exit_code(output, _terminal_rows()), 0)

    def test_idle_terminal_no_tools_ran_returns_0(self):
        output = _make_output(idle_reached=True, signal="no_tools_ran")
        self.assertEqual(_compute_phase2_exit_code(output, _terminal_rows()), 0)

    def test_idle_terminal_partial_block_returns_0(self):
        output = _make_output(idle_reached=True, signal="partial_block")
        self.assertEqual(_compute_phase2_exit_code(output, _terminal_rows()), 0)

    def test_idle_terminal_phase2_absent_returns_0(self):
        output = _make_output(idle_reached=True, signal="phase2_absent")
        self.assertEqual(_compute_phase2_exit_code(output, _terminal_rows()), 0)

    def test_idle_terminal_failed_status_ok_signal_returns_0(self):
        rows = [{"result": {"status": "failed"}}]
        output = _make_output(idle_reached=True, signal="ok")
        self.assertEqual(_compute_phase2_exit_code(output, rows), 0)

    def test_idle_missing_signal_key_returns_0(self):
        output = {"idle_reached": True}
        self.assertEqual(_compute_phase2_exit_code(output, _terminal_rows()), 0)


if __name__ == "__main__":
    unittest.main()
