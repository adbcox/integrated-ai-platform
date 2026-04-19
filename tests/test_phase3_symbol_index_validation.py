"""Tests for the phase3_symbol_index_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPhase3SymbolIndexValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase3_symbol_index_validation_report import (
            generate_phase3_symbol_index_validation_report,
        )
        return generate_phase3_symbol_index_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"all_checks_pass is False. report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("importable"), f"report={report}")

    def test_empty_input_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("empty_input_ok"), f"report={report}")

    def test_no_symbols_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("no_symbols_ok"), f"report={report}")

    def test_class_extraction_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("class_extraction_ok"), f"report={report}")

    def test_def_extraction_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("def_extraction_ok"), f"report={report}")

    def test_dedup_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("dedup_ok"), f"report={report}")

    def test_all_contains(self):
        report = self._run_report()
        self.assertTrue(report.get("all_contains"), f"report={report}")

    def test_bin_wires_symbol_index(self):
        report = self._run_report()
        self.assertTrue(report.get("bin_wires_symbol_index"), f"report={report}")

    def test_no_failures(self):
        report = self._run_report()
        self.assertEqual(report.get("failures"), [], f"report={report}")


if __name__ == "__main__":
    unittest.main()
