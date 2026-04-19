"""Tests for the phase3_auto_continue_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPhase3AutoContinueValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase3_auto_continue_validation_report import (
            generate_phase3_auto_continue_validation_report,
        )
        return generate_phase3_auto_continue_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"all_checks_pass is False. report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_helper_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("helper_importable"), f"report={report}")

    def test_flag_registered(self):
        report = self._run_report()
        self.assertTrue(report.get("flag_registered"), f"report={report}")

    def test_trigger_set_correct(self):
        report = self._run_report()
        self.assertTrue(report.get("trigger_set_correct"), f"report={report}")

    def test_return_keys_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("return_keys_ok"), f"report={report}")

    def test_error_captured_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("error_captured_ok"), f"report={report}")

    def test_template_used_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("template_used_ok"), f"report={report}")

    def test_bin_wires_continuation(self):
        report = self._run_report()
        self.assertTrue(report.get("bin_wires_continuation"), f"report={report}")

    def test_choices_includes_flag(self):
        report = self._run_report()
        self.assertTrue(report.get("choices_includes_flag"), f"report={report}")

    def test_ran_false_on_error(self):
        report = self._run_report()
        self.assertTrue(report.get("ran_false_on_error"), f"report={report}")

    def test_no_failures(self):
        report = self._run_report()
        self.assertEqual(report.get("failures"), [], f"report={report}")


if __name__ == "__main__":
    unittest.main()
