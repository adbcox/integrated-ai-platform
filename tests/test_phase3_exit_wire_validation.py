"""Tests for the phase3_exit_wire_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPhase3ExitWireValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase3_exit_wire_validation_report import (
            generate_phase3_exit_wire_validation_report,
        )
        return generate_phase3_exit_wire_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"all_checks_pass is False. report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("importable"), f"report={report}")

    def test_refine_returns_five(self):
        report = self._run_report()
        self.assertTrue(report.get("refine_returns_five"), f"report={report}")

    def test_insufficient_returns_six(self):
        report = self._run_report()
        self.assertTrue(report.get("insufficient_returns_six"), f"report={report}")

    def test_ready_returns_zero(self):
        report = self._run_report()
        self.assertTrue(report.get("ready_returns_zero"), f"report={report}")

    def test_empty_returns_zero(self):
        report = self._run_report()
        self.assertTrue(report.get("empty_returns_zero"), f"report={report}")

    def test_none_action_returns_zero(self):
        report = self._run_report()
        self.assertTrue(report.get("none_action_returns_zero"), f"report={report}")

    def test_non_dict_safe(self):
        report = self._run_report()
        self.assertTrue(report.get("non_dict_safe"), f"report={report}")

    def test_phase2_nonzero_not_overridden(self):
        report = self._run_report()
        self.assertTrue(report.get("phase2_nonzero_not_overridden"), f"report={report}")

    def test_phase2_zero_phase3_applied(self):
        report = self._run_report()
        self.assertTrue(report.get("phase2_zero_phase3_applied"), f"report={report}")

    def test_bin_wires_compute(self):
        report = self._run_report()
        self.assertTrue(report.get("bin_wires_compute"), f"report={report}")

    def test_no_failures(self):
        report = self._run_report()
        self.assertEqual(report.get("failures"), [], f"report={report}")


if __name__ == "__main__":
    unittest.main()
