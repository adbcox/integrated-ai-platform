"""Tests for the phase2_exit_wire_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestPhase2ExitWireValidation(unittest.TestCase):
    def _run_report(self) -> dict:
        from artifacts.phase2_exit_wire_validation_report import (
            generate_phase2_exit_wire_validation_report,
        )
        return generate_phase2_exit_wire_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_helper_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("helper_importable"), f"report={report}")

    def test_cases_checked_ge_11(self):
        report = self._run_report()
        self.assertGreaterEqual(report.get("cases_checked", 0), 11, f"report={report}")


if __name__ == "__main__":
    unittest.main()
