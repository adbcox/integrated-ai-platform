"""Tests for the phase3_context_bundle_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPhase3ContextBundleValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase3_context_bundle_validation_report import (
            generate_phase3_context_bundle_validation_report,
        )
        return generate_phase3_context_bundle_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"all_checks_pass is False. report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("importable"), f"report={report}")

    def test_empty_inputs_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("empty_inputs_ok"), f"report={report}")

    def test_total_files_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("total_files_ok"), f"report={report}")

    def test_total_symbols_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("total_symbols_ok"), f"report={report}")

    def test_top_file_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("top_file_ok"), f"report={report}")

    def test_prompt_ready_true_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("prompt_ready_true_ok"), f"report={report}")

    def test_prompt_ready_false_no_query_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("prompt_ready_false_no_query_ok"), f"report={report}")

    def test_join_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("join_ok"), f"report={report}")

    def test_all_contains(self):
        report = self._run_report()
        self.assertTrue(report.get("all_contains"), f"report={report}")

    def test_bin_wires_context_bundle(self):
        report = self._run_report()
        self.assertTrue(report.get("bin_wires_context_bundle"), f"report={report}")

    def test_no_failures(self):
        report = self._run_report()
        self.assertEqual(report.get("failures"), [], f"report={report}")


if __name__ == "__main__":
    unittest.main()
