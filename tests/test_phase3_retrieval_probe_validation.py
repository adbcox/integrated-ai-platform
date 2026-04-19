"""Tests for the phase3_retrieval_probe_validation_report artifact."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestPhase3RetrievalProbeValidation(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def _run_report(self):
        from artifacts.phase3_retrieval_probe_validation_report import (
            generate_phase3_retrieval_probe_validation_report,
        )
        return generate_phase3_retrieval_probe_validation_report()

    def test_all_checks_pass(self):
        report = self._run_report()
        self.assertTrue(
            report.get("all_checks_pass"),
            f"all_checks_pass is False. report={report}",
        )

    def test_status_pass(self):
        report = self._run_report()
        self.assertEqual(report.get("status"), "pass", f"report={report}")

    def test_search_contract_present(self):
        report = self._run_report()
        self.assertTrue(report.get("search_contract_present"), f"report={report}")

    def test_repo_map_contract_present(self):
        report = self._run_report()
        self.assertTrue(report.get("repo_map_contract_present"), f"report={report}")

    def test_apply_patch_contract_present(self):
        report = self._run_report()
        self.assertTrue(report.get("apply_patch_contract_present"), f"report={report}")

    def test_search_query_correct(self):
        report = self._run_report()
        self.assertTrue(report.get("search_query_correct"), f"report={report}")

    def test_repo_map_path_correct(self):
        report = self._run_report()
        self.assertTrue(report.get("repo_map_path_correct"), f"report={report}")

    def test_build_job_has_three_typed_tools(self):
        report = self._run_report()
        self.assertTrue(report.get("build_job_has_three_typed_tools"), f"report={report}")

    def test_retrieval_probe_in_choices(self):
        report = self._run_report()
        self.assertTrue(report.get("retrieval_probe_in_choices"), f"report={report}")


if __name__ == "__main__":
    unittest.main()
