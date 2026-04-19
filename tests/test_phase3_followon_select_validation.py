"""Tests for the phase3_followon_select_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPhase3FollowonSelectValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase3_followon_select_validation_report import (
            generate_phase3_followon_select_validation_report,
        )
        return generate_phase3_followon_select_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(report.get("all_checks_pass"), f"all_checks_pass is False. report={report}")

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("importable"), f"report={report}")

    def test_ready_maps_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("ready_maps_ok"), f"report={report}")

    def test_insufficient_context_maps_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("insufficient_context_maps_ok"), f"report={report}")

    def test_refine_retrieval_maps_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("refine_retrieval_maps_ok"), f"report={report}")

    def test_no_context_maps_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("no_context_maps_ok"), f"report={report}")

    def test_unknown_maps_safe(self):
        report = self._run_report()
        self.assertTrue(report.get("unknown_maps_safe"), f"report={report}")

    def test_non_dict_safe(self):
        report = self._run_report()
        self.assertTrue(report.get("non_dict_safe"), f"report={report}")

    def test_all_contains(self):
        report = self._run_report()
        self.assertTrue(report.get("all_contains"), f"report={report}")

    def test_loader_importable(self):
        report = self._run_report()
        self.assertTrue(report.get("loader_importable"), f"report={report}")

    def test_loader_missing_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("loader_missing_ok"), f"report={report}")

    def test_template_dispatches(self):
        report = self._run_report()
        self.assertTrue(report.get("template_dispatches"), f"report={report}")

    def test_dispatch_guard_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("dispatch_guard_ok"), f"report={report}")

    def test_bin_wires_followon(self):
        report = self._run_report()
        self.assertTrue(report.get("bin_wires_followon"), f"report={report}")

    def test_choices_ok(self):
        report = self._run_report()
        self.assertTrue(report.get("choices_ok"), f"report={report}")

    def test_no_failures(self):
        report = self._run_report()
        self.assertEqual(report.get("failures"), [], f"report={report}")


if __name__ == "__main__":
    unittest.main()
