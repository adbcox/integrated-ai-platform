"""Offline coverage for TREV-MC-1 MC family tactical unlock review."""

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


class McFamilyUnlockReviewTest(unittest.TestCase):
    def test_review_file_exists_and_is_remains_locked(self) -> None:
        review = _load("mc_family_unlock_review.json")
        self.assertEqual(review["family_id"], "mc")
        self.assertEqual(review["packet_id"], "TREV-MC-1")
        self.assertEqual(review["review_decision"], "remains_locked")
        self.assertEqual(review["review_class"], "tactical_review")
        self.assertEqual(review["post_review_state"]["unlock_state"], "locked")
        self.assertEqual(
            review["post_review_state"]["classification"], "provisional_precursor"
        )
        self.assertEqual(review["post_review_state"]["canonical_phase_dependency"], 4)

    def test_review_precondition_counts_agree_with_booleans(self) -> None:
        review = _load("mc_family_unlock_review.json")
        self.assertEqual(review["preconditions_total"], 3)
        bools = [p["met"] for p in review["precondition_evaluation"]]
        self.assertEqual(len(bools), 3)
        self.assertEqual(review["preconditions_met"], sum(1 for b in bools if b))

    def test_review_records_zero_preconditions_met(self) -> None:
        review = _load("mc_family_unlock_review.json")
        self.assertEqual(review["preconditions_met"], 0)
        self.assertEqual(
            [p["met"] for p in review["precondition_evaluation"]],
            [False, False, False],
        )

    def test_no_mc_test_fixture_exists(self) -> None:
        mc_tests = [
            p
            for p in _git_ls_files()
            if p.startswith("tests/") and Path(p).name.startswith("test_mc_")
        ]
        self.assertEqual(mc_tests, [])

    def test_no_mc_prefixed_framework_files_exist(self) -> None:
        mc_framework = [
            p
            for p in _git_ls_files()
            if p.startswith("framework/") and Path(p).name.startswith("mc_")
        ]
        self.assertEqual(mc_framework, [])

    def test_unlock_criteria_mc_row_is_unchanged(self) -> None:
        unlock = _load("tactical_unlock_criteria.json")
        mc = next((f for f in unlock["families"] if f["family_id"] == "mc"), None)
        self.assertIsNotNone(mc)
        assert mc is not None
        self.assertEqual(mc["unlock_state"], "locked")
        self.assertTrue(mc["review_packet_required"])
        self.assertEqual(mc["currently_met_preconditions"], [])
        self.assertEqual(mc["prefixes"], ["mc_", "multi_phase_"])

    def test_family_classification_mc_row_is_unchanged(self) -> None:
        classification = _load("tactical_family_classification.json")
        mc = next(
            (f for f in classification["families"] if f["family_id"] == "mc"), None
        )
        self.assertIsNotNone(mc)
        assert mc is not None
        self.assertEqual(mc["current_classification"], "provisional_precursor")
        self.assertEqual(mc["canonical_phase_dependency"], 4)

    def test_runtime_adoption_report_mc_row_is_zero_adoption(self) -> None:
        report = _load("runtime_adoption_report.json")
        mc = next(
            (r for r in report["tactical_family_adoption"] if r["family_id"] == "mc"),
            None,
        )
        self.assertIsNotNone(mc)
        assert mc is not None
        self.assertEqual(mc["adopting_files"], 0)
        self.assertEqual(mc["adopting_paths"], [])

    def test_phase_4_remains_open_and_unadvanced(self) -> None:
        roadmap = _load("canonical_roadmap.json")
        p4 = next((p for p in roadmap["phases"] if p["phase_id"] == 4), None)
        self.assertIsNotNone(p4)
        assert p4 is not None
        self.assertEqual(p4["status"], "open")

    def test_adr_0012_is_committed(self) -> None:
        self.assertTrue(
            (GOV_DIR / "authority_adr_0012_mc_family_unlock_review.md").exists()
        )

    def test_review_preserves_current_allowed_class(self) -> None:
        nextc = _load("next_package_class.json")
        self.assertEqual(nextc["current_allowed_class"], "ratification_only")

    def test_review_preserves_phase2_closed_state(self) -> None:
        phase2 = _load("phase2_adoption_decision.json")
        self.assertEqual(phase2["decision"], "closed")


if __name__ == "__main__":
    unittest.main()
