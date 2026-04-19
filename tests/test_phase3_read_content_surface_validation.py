"""Tests for the phase3_read_content_surface_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPhase3ReadContentSurfaceValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase3_read_content_surface_validation_report import (
            generate_phase3_read_content_surface_validation_report,
        )
        return generate_phase3_read_content_surface_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"all_checks_pass is False. report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_extract_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("extract_importable"), f"report={report}")

    def test_summary_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("summary_importable"), f"report={report}")

    def test_extract_empty_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("extract_empty_ok"), f"report={report}")

    def test_extract_read_file_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("extract_read_file_ok"), f"report={report}")

    def test_extract_non_read_excluded(self):
        report = self._run_report()
        self.assertTrue(report.get("extract_non_read_excluded"), f"report={report}")

    def test_summary_keys_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("summary_keys_ok"), f"report={report}")

    def test_summary_counts_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("summary_counts_ok"), f"report={report}")

    def test_main_wires_read_content(self):
        report = self._run_report()
        self.assertTrue(report.get("main_wires_read_content"), f"report={report}")

    def test_no_failures(self):
        report = self._run_report()
        self.assertEqual(report.get("failures"), [], f"report={report}")


if __name__ == "__main__":
    unittest.main()
