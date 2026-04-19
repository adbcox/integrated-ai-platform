"""Tests for the phase3_read_after_retrieval_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestPhase3ReadAfterRetrievalValidation(unittest.TestCase):
    def _run_report(self) -> dict:
        from artifacts.phase3_read_after_retrieval_validation_report import (
            generate_phase3_read_after_retrieval_validation_report,
        )
        return generate_phase3_read_after_retrieval_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_loader_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("loader_importable"), f"report={report}")

    def test_template_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("template_importable"), f"report={report}")

    def test_load_missing_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("load_missing_ok"), f"report={report}")

    def test_load_valid_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("load_valid_ok"), f"report={report}")

    def test_template_no_targets_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("template_no_targets_ok"), f"report={report}")

    def test_template_with_targets_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("template_with_targets_ok"), f"report={report}")

    def test_dispatch_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("dispatch_ok"), f"report={report}")

    def test_choices_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("choices_ok"), f"report={report}")


if __name__ == "__main__":
    unittest.main()
