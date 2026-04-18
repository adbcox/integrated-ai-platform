"""Tests for the phase2_manager_wire_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


class TestPhase2ManagerWireValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase2_manager_wire_validation_report import (
            generate_phase2_manager_wire_validation_report,
        )
        return generate_phase2_manager_wire_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(
            report.get("all_checks_pass"),
            f"all_checks_pass is False. report={report}",
        )

    def test_status_pass_and_all_presence_booleans_true(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")
        for key in (
            "manager_view_present",
            "canonical_session_summary_present",
            "canonical_job_summaries_present",
            "typed_tool_summary_present",
            "permission_decision_count_present",
            "final_outcome_present",
            "tool_count_ge_1",
        ):
            self.assertTrue(report.get(key), f"{key} is False. report={report}")


if __name__ == "__main__":
    unittest.main()
