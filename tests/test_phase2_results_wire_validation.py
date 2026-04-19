"""Tests for the phase2_results_wire_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestPhase2ResultsWireValidation(unittest.TestCase):
    def _run_report(self) -> dict:
        from artifacts.phase2_results_wire_validation_report import (
            generate_phase2_results_wire_validation_report,
        )
        return generate_phase2_results_wire_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_extractor_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("extractor_importable"), f"report={report}")

    def test_observation_extraction_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("observation_extraction_ok"), f"report={report}")

    def test_empty_payload_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("empty_payload_ok"), f"report={report}")

    def test_action_exclusion_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("action_exclusion_ok"), f"report={report}")

    def test_bin_import_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("bin_import_ok"), f"report={report}")


if __name__ == "__main__":
    unittest.main()
