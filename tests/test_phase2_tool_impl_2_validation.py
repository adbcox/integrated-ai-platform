"""Tests for the phase2_tool_impl_2_validation_report artifact."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


class TestPhase2ToolImpl2Validation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        self._tmp = tempfile.mkdtemp(prefix="p2_tool_impl2_val_")

    def _run_report(self):
        from artifacts.phase2_tool_impl_2_validation_report import (
            generate_phase2_tool_impl_2_validation_report,
        )
        return generate_phase2_tool_impl_2_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(
            report.get("all_checks_pass"),
            f"all_checks_pass is False. report={report}",
        )

    def test_status_is_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass")

    def test_allowed_payload_ok(self):
        report = self._run_report()
        self.assertTrue(
            report.get("allowed_payload_ok"),
            f"allowed_payload_ok is False. report={report}",
        )

    def test_blocked_payload_ok(self):
        report = self._run_report()
        self.assertTrue(
            report.get("blocked_payload_ok"),
            f"blocked_payload_ok is False. report={report}",
        )

    def test_required_tools_in_observed_allowed(self):
        report = self._run_report()
        required = report.get("required_tools", [])
        observed = report.get("tools_observed_allowed", [])
        for tool in required:
            self.assertIn(
                tool, observed,
                f"Required tool '{tool}' not in tools_observed_allowed={observed}",
            )


if __name__ == "__main__":
    unittest.main()
