"""Tests for the phase3_retrieval_consume_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPhase3RetrievalConsumeValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase3_retrieval_consume_validation_report import (
            generate_phase3_retrieval_consume_validation_report,
        )
        return generate_phase3_retrieval_consume_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"all_checks_pass is False. report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_derive_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("derive_importable"), f"report={report}")

    def test_summary_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("summary_importable"), f"report={report}")

    def test_derive_empty_input_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("derive_empty_input_ok"), f"report={report}")

    def test_derive_extracts_path_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("derive_extracts_path_ok"), f"report={report}")

    def test_derive_deduplication_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("derive_deduplication_ok"), f"report={report}")

    def test_derive_max_files_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("derive_max_files_ok"), f"report={report}")

    def test_summary_empty_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("summary_empty_ok"), f"report={report}")

    def test_summary_query_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("summary_query_ok"), f"report={report}")

    def test_summary_read_targets_count_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("summary_read_targets_count_ok"), f"report={report}")

    def test_bin_imports_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("bin_imports_ok"), f"report={report}")


if __name__ == "__main__":
    unittest.main()
