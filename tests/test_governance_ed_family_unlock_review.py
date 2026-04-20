"""Offline coverage for TREV-ED-1 ED family tactical unlock review."""

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


class EdFamilyUnlockReviewTest(unittest.TestCase):
    def test_review_file_exists_and_is_remains_locked(self) -> None:
        review = _load("ed_family_unlock_review.json")
        self.assertEqual(review["family_id"], "ed")
        self.assertEqual(review["packet_id"], "TREV-ED-1")
        self.assertEqual(review["review_decision"], "remains_locked")
        self.assertEqual(review["review_class"], "tactical_review")
        self.assertEqual(review["post_review_state"]["unlock_state"], "locked")
        self.assertEqual(
            review["post_review_state"]["classification"], "provisional_precursor"
        )

    def test_review_precondition_counts_agree_with_booleans(self) -> None:
        review = _load("ed_family_unlock_review.json")
        self.assertEqual(review["preconditions_total"], 3)
        bools = [p["met"] for p in review["precondition_evaluation"]]
        self.assertEqual(len(bools), 3)
        self.assertEqual(review["preconditions_met"], sum(1 for b in bools if b))

    def test_review_records_zero_preconditions_met(self) -> None:
        review = _load("ed_family_unlock_review.json")
        self.assertEqual(review["preconditions_met"], 0)
        self.assertEqual(
            [p["met"] for p in review["precondition_evaluation"]],
            [False, False, False],
        )

    def test_no_ed_framework_files_exist(self) -> None:
        ed_framework = [
            p
            for p in _git_ls_files()
            if p.startswith("framework/") and Path(p).name.startswith("ed_")
        ]
        self.assertEqual(ed_framework, [])

    def test_no_ed_test_fixture_exists(self) -> None:
        ed_tests = [
            p
            for p in _git_ls_files()
            if p.startswith("tests/") and Path(p).name.startswith("test_ed_")
        ]
        self.assertEqual(ed_tests, [])

    def test_unlock_criteria_ed_row_is_unchanged(self) -> None:
        unlock = _load("tactical_unlock_criteria.json")
        ed = next((f for f in unlock["families"] if f["family_id"] == "ed"), None)
        self.assertIsNotNone(ed)
        assert ed is not None
        self.assertEqual(ed["unlock_state"], "locked")
        self.assertTrue(ed["review_packet_required"])
        self.assertEqual(ed["currently_met_preconditions"], [])

    def test_family_classification_ed_row_is_unchanged(self) -> None:
        classification = _load("tactical_family_classification.json")
        ed = next(
            (f for f in classification["families"] if f["family_id"] == "ed"), None
        )
        self.assertIsNotNone(ed)
        assert ed is not None
        self.assertEqual(ed["current_classification"], "provisional_precursor")
        self.assertEqual(ed["canonical_phase_dependency"], 2)

    def test_runtime_adoption_report_ed_row_is_zero(self) -> None:
        report = _load("runtime_adoption_report.json")
        ed = next(
            (r for r in report["tactical_family_adoption"] if r["family_id"] == "ed"),
            None,
        )
        self.assertIsNotNone(ed)
        assert ed is not None
        self.assertEqual(ed["adopting_files"], 0)
        self.assertEqual(ed["adopting_paths"], [])

    def test_adr_0011_is_committed(self) -> None:
        self.assertTrue(
            (GOV_DIR / "authority_adr_0011_ed_family_unlock_review.md").exists()
        )

    def test_review_preserves_current_allowed_class(self) -> None:
        nextc = _load("next_package_class.json")
        self.assertIn(nextc["current_allowed_class"], {"ratification_only", "capability_session"})

    def test_review_preserves_phase2_closed_state(self) -> None:
        phase2 = _load("phase2_adoption_decision.json")
        self.assertEqual(phase2["decision"], "closed")


if __name__ == "__main__":
    unittest.main()
