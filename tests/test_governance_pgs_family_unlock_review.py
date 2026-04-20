"""Offline coverage for TREV-PGS-1 PGS family tactical unlock review."""

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


class PgsFamilyUnlockReviewTest(unittest.TestCase):
    def test_review_file_exists_and_is_remains_locked(self) -> None:
        review = _load("pgs_family_unlock_review.json")
        self.assertEqual(review["family_id"], "pgs")
        self.assertEqual(review["packet_id"], "TREV-PGS-1")
        self.assertEqual(review["review_decision"], "remains_locked")
        self.assertEqual(review["review_class"], "tactical_review")
        self.assertEqual(review["post_review_state"]["unlock_state"], "locked")
        self.assertEqual(
            review["post_review_state"]["classification"], "provisional_precursor"
        )
        self.assertEqual(review["post_review_state"]["canonical_phase_dependency"], 5)

    def test_review_precondition_counts_agree_with_booleans(self) -> None:
        review = _load("pgs_family_unlock_review.json")
        self.assertEqual(review["preconditions_total"], 3)
        bools = [p["met"] for p in review["precondition_evaluation"]]
        self.assertEqual(len(bools), 3)
        self.assertEqual(review["preconditions_met"], sum(1 for b in bools if b))

    def test_review_records_zero_preconditions_met(self) -> None:
        review = _load("pgs_family_unlock_review.json")
        self.assertEqual(review["preconditions_met"], 0)
        self.assertEqual(
            [p["met"] for p in review["precondition_evaluation"]],
            [False, False, False],
        )

    def test_review_reflects_real_pgs_surface(self) -> None:
        review = _load("pgs_family_unlock_review.json")
        pgs_files = [
            p
            for p in _git_ls_files()
            if p.startswith("framework/") and Path(p).name.startswith("pgs_")
        ]
        self.assertGreater(
            len(pgs_files),
            0,
            "expected a real pgs surface under framework/ at baseline",
        )
        self.assertEqual(
            review["surface_observation"]["pgs_framework_file_count"],
            len(pgs_files),
        )

    def test_no_pgs_test_fixture_exists(self) -> None:
        pgs_tests = [
            p
            for p in _git_ls_files()
            if p.startswith("tests/") and Path(p).name.startswith("test_pgs_")
        ]
        self.assertEqual(pgs_tests, [])

    def test_no_pgs_case_in_offline_scenarios(self) -> None:
        path = REPO_ROOT / "tests" / "run_offline_scenarios.sh"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        self.assertNotIn("pgs_", text)

    def test_unlock_criteria_pgs_row_is_unchanged(self) -> None:
        unlock = _load("tactical_unlock_criteria.json")
        pgs = next((f for f in unlock["families"] if f["family_id"] == "pgs"), None)
        self.assertIsNotNone(pgs)
        assert pgs is not None
        self.assertEqual(pgs["unlock_state"], "locked")
        self.assertTrue(pgs["review_packet_required"])
        self.assertEqual(pgs["currently_met_preconditions"], [])
        self.assertEqual(pgs["prefixes"], ["pgs_"])

    def test_family_classification_pgs_row_is_unchanged(self) -> None:
        classification = _load("tactical_family_classification.json")
        pgs = next(
            (f for f in classification["families"] if f["family_id"] == "pgs"), None
        )
        self.assertIsNotNone(pgs)
        assert pgs is not None
        self.assertEqual(pgs["current_classification"], "provisional_precursor")
        self.assertEqual(pgs["canonical_phase_dependency"], 5)

    def test_runtime_adoption_report_pgs_row_is_zero_adoption(self) -> None:
        report = _load("runtime_adoption_report.json")
        pgs = next(
            (r for r in report["tactical_family_adoption"] if r["family_id"] == "pgs"),
            None,
        )
        self.assertIsNotNone(pgs)
        assert pgs is not None
        self.assertEqual(pgs["adopting_files"], 0)
        self.assertEqual(pgs["adopting_paths"], [])

    def test_phase_5_remains_open_and_unadvanced(self) -> None:
        roadmap = _load("canonical_roadmap.json")
        p5 = next((p for p in roadmap["phases"] if p["phase_id"] == 5), None)
        self.assertIsNotNone(p5)
        assert p5 is not None
        self.assertEqual(p5["status"], "open")

    def test_adr_0015_is_committed(self) -> None:
        self.assertTrue(
            (GOV_DIR / "authority_adr_0015_pgs_family_unlock_review.md").exists()
        )

    def test_lob_w3_pause_invariant_preserved(self) -> None:
        review = _load("pgs_family_unlock_review.json")
        self.assertTrue(review["invariants_preserved"]["lob_w3_pause_preserved"])
        adr_path = GOV_DIR / "authority_adr_0003_lob_w3_classification.md"
        self.assertTrue(adr_path.exists())

    def test_review_preserves_current_allowed_class(self) -> None:
        nextc = _load("next_package_class.json")
        self.assertIn(nextc["current_allowed_class"], {"ratification_only", "capability_session"})

    def test_review_preserves_phase2_closed_state(self) -> None:
        phase2 = _load("phase2_adoption_decision.json")
        self.assertEqual(phase2["decision"], "closed")


if __name__ == "__main__":
    unittest.main()
