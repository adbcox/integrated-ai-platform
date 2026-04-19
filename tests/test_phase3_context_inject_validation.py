"""Tests for the phase3_context_inject_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPhase3ContextInjectValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase3_context_inject_validation_report import (
            generate_phase3_context_inject_validation_report,
        )
        return generate_phase3_context_inject_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"all_checks_pass is False. report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("importable"), f"report={report}")

    def test_empty_bundle_returns_empty(self):
        report = self._run_report()
        self.assertTrue(report.get("empty_bundle_returns_empty"), f"report={report}")

    def test_no_query_returns_empty(self):
        report = self._run_report()
        self.assertTrue(report.get("no_query_returns_empty"), f"report={report}")

    def test_valid_bundle_produces_prompt(self):
        report = self._run_report()
        self.assertTrue(report.get("valid_bundle_produces_prompt"), f"report={report}")

    def test_classes_in_prompt(self):
        report = self._run_report()
        self.assertTrue(report.get("classes_in_prompt"), f"report={report}")

    def test_functions_in_prompt(self):
        report = self._run_report()
        self.assertTrue(report.get("functions_in_prompt"), f"report={report}")

    def test_loader_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("loader_importable"), f"report={report}")

    def test_loader_missing_returns_empty(self):
        report = self._run_report()
        self.assertTrue(report.get("loader_missing_returns_empty"), f"report={report}")

    def test_template_dispatches(self):
        report = self._run_report()
        self.assertTrue(report.get("template_dispatches"), f"report={report}")

    def test_all_contains(self):
        report = self._run_report()
        self.assertTrue(report.get("all_contains"), f"report={report}")

    def test_bin_wires_persistence(self):
        report = self._run_report()
        self.assertTrue(report.get("bin_wires_persistence"), f"report={report}")

    def test_choices_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("choices_ok"), f"report={report}")

    def test_no_failures(self):
        report = self._run_report()
        self.assertEqual(report.get("failures"), [], f"report={report}")


if __name__ == "__main__":
    unittest.main()
