"""Offline coverage for TREV-EO-1 EO family tactical unlock review."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"


def _load(name: str) -> dict:
    return json.loads((GOV_DIR / name).read_text(encoding="utf-8"))


def _git_ls_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True)
    return [line for line in out.splitlines() if line]


class EoFamilyUnlockReviewTest(unittest.TestCase):
    def test_review_file_exists_and_is_remains_locked(self) -> None:
        review = _load("eo_family_unlock_review.json")
        self.assertEqual(review["family_id"], "eo")
        self.assertEqual(review["packet_id"], "TREV-EO-1")
        self.assertEqual(review["review_decision"], "remains_locked")
        self.assertEqual(review["review_class"], "tactical_review")
        self.assertEqual(review["post_review_state"]["unlock_state"], "locked")
        self.assertEqual(
            review["post_review_state"]["classification"], "provisional_precursor"
        )

    def test_review_records_zero_preconditions_met(self) -> None:
        review = _load("eo_family_unlock_review.json")
        self.assertEqual(review["preconditions_total"], 3)
        self.assertEqual(review["preconditions_met"], 0)
        self.assertEqual(
            [p["met"] for p in review["precondition_evaluation"]],
            [False, False, False],
        )

    def test_no_eo_framework_files_exist(self) -> None:
        eo_framework = [
            p
            for p in _git_ls_files()
            if p.startswith("framework/") and Path(p).name.startswith("eo_")
        ]
        self.assertEqual(eo_framework, [])

    def test_no_eo_test_fixture_exists(self) -> None:
        eo_tests = [
            p
            for p in _git_ls_files()
            if p.startswith("tests/") and Path(p).name.startswith("test_eo_")
        ]
        self.assertEqual(eo_tests, [])

    def test_unlock_criteria_eo_row_is_unchanged(self) -> None:
        unlock = _load("tactical_unlock_criteria.json")
        eo = next((f for f in unlock["families"] if f["family_id"] == "eo"), None)
        self.assertIsNotNone(eo)
        assert eo is not None
        self.assertEqual(eo["unlock_state"], "locked")
        self.assertTrue(eo["review_packet_required"])
        self.assertEqual(eo["currently_met_preconditions"], [])

    def test_family_classification_eo_row_is_unchanged(self) -> None:
        classification = _load("tactical_family_classification.json")
        eo = next(
            (f for f in classification["families"] if f["family_id"] == "eo"), None
        )
        self.assertIsNotNone(eo)
        assert eo is not None
        self.assertEqual(eo["current_classification"], "provisional_precursor")

    def test_runtime_adoption_report_eo_row_is_zero(self) -> None:
        report = _load("runtime_adoption_report.json")
        eo = next(
            (r for r in report["tactical_family_adoption"] if r["family_id"] == "eo"),
            None,
        )
        self.assertIsNotNone(eo)
        assert eo is not None
        self.assertEqual(eo["adopting_files"], 0)
        self.assertEqual(eo["adopting_paths"], [])

    def test_adr_0010_is_committed(self) -> None:
        self.assertTrue(
            (GOV_DIR / "authority_adr_0010_eo_family_unlock_review.md").exists()
        )

    def test_review_preserves_current_allowed_class(self) -> None:
        nextc = _load("next_package_class.json")
        self.assertIn(nextc["current_allowed_class"], {"ratification_only", "capability_session"})

    def test_review_preserves_phase2_closed_state(self) -> None:
        phase2 = _load("phase2_adoption_decision.json")
        self.assertEqual(phase2["decision"], "closed")


if __name__ == "__main__":
    unittest.main()
