"""Tests for the phase3_inference_response_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPhase3InferenceResponseValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase3_inference_response_validation_report import (
            generate_phase3_inference_response_validation_report,
        )
        return generate_phase3_inference_response_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"all_checks_pass is False. report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("importable"), f"report={report}")

    def test_empty_payload_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("empty_payload_ok"), f"report={report}")

    def test_output_text_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("output_text_ok"), f"report={report}")

    def test_has_content_false_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("has_content_false_ok"), f"report={report}")

    def test_output_chars_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("output_chars_ok"), f"report={report}")

    def test_non_dict_safe(self):
        report = self._run_report()
        self.assertTrue(report.get("non_dict_safe"), f"report={report}")

    def test_all_contains(self):
        report = self._run_report()
        self.assertTrue(report.get("all_contains"), f"report={report}")

    def test_template_dispatches(self):
        report = self._run_report()
        self.assertTrue(report.get("template_dispatches"), f"report={report}")

    def test_bin_wires_inference_response(self):
        report = self._run_report()
        self.assertTrue(report.get("bin_wires_inference_response"), f"report={report}")

    def test_choices_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("choices_ok"), f"report={report}")

    def test_no_failures(self):
        report = self._run_report()
        self.assertEqual(report.get("failures"), [], f"report={report}")


if __name__ == "__main__":
    unittest.main()
