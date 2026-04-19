"""Tests for the phase3_next_action_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPhase3NextActionValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase3_next_action_validation_report import (
            generate_phase3_next_action_validation_report,
        )
        return generate_phase3_next_action_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"all_checks_pass is False. report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("importable"), f"report={report}")

    def test_no_context_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("no_context_ok"), f"report={report}")

    def test_insufficient_context_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("insufficient_context_ok"), f"report={report}")

    def test_refine_retrieval_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("refine_retrieval_ok"), f"report={report}")

    def test_ready_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("ready_ok"), f"report={report}")

    def test_required_keys_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("required_keys_ok"), f"report={report}")

    def test_non_dict_safe(self):
        report = self._run_report()
        self.assertTrue(report.get("non_dict_safe"), f"report={report}")

    def test_all_contains(self):
        report = self._run_report()
        self.assertTrue(report.get("all_contains"), f"report={report}")

    def test_bin_wires_next_action(self):
        report = self._run_report()
        self.assertTrue(report.get("bin_wires_next_action"), f"report={report}")

    def test_action_values_bounded(self):
        report = self._run_report()
        self.assertTrue(report.get("action_values_bounded"), f"report={report}")

    def test_no_failures(self):
        report = self._run_report()
        self.assertEqual(report.get("failures"), [], f"report={report}")


if __name__ == "__main__":
    unittest.main()
