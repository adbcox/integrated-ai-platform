"""Tests for the phase2_manager_decision_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


class TestPhase2ManagerDecisionValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase2_manager_decision_validation_report import (
            generate_phase2_manager_decision_validation_report,
        )
        return generate_phase2_manager_decision_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(
            report.get("all_checks_pass"),
            f"all_checks_pass is False. report={report}",
        )

    def test_status_pass_signal_valid_payload_present(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")
        self.assertTrue(report.get("signal_value_valid"), f"report={report}")
        self.assertTrue(report.get("phase2_payload_present"), f"report={report}")


if __name__ == "__main__":
    unittest.main()
