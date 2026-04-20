"""Offline coverage for TREV-LIVE_BRIDGE-1 LIVE_BRIDGE family tactical unlock review."""

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


class LiveBridgeFamilyUnlockReviewTest(unittest.TestCase):
    def test_review_file_exists_and_is_remains_locked(self) -> None:
        review = _load("live_bridge_family_unlock_review.json")
        self.assertEqual(review["family_id"], "live_bridge")
        self.assertEqual(review["packet_id"], "TREV-LIVE_BRIDGE-1")
        self.assertEqual(review["review_decision"], "remains_locked")
        self.assertEqual(review["review_class"], "tactical_review")
        self.assertEqual(review["post_review_state"]["unlock_state"], "locked")
        self.assertEqual(
            review["post_review_state"]["classification"], "provisional_precursor"
        )
        self.assertEqual(review["post_review_state"]["canonical_phase_dependency"], 6)

    def test_review_precondition_counts_agree_with_booleans(self) -> None:
        review = _load("live_bridge_family_unlock_review.json")
        self.assertEqual(review["preconditions_total"], 3)
        bools = [p["met"] for p in review["precondition_evaluation"]]
        self.assertEqual(len(bools), 3)
        self.assertEqual(review["preconditions_met"], sum(1 for b in bools if b))

    def test_review_records_zero_preconditions_met(self) -> None:
        review = _load("live_bridge_family_unlock_review.json")
        self.assertEqual(review["preconditions_met"], 0)
        self.assertEqual(
            [p["met"] for p in review["precondition_evaluation"]],
            [False, False, False],
        )

    def test_review_reflects_real_live_bridge_surface(self) -> None:
        review = _load("live_bridge_family_unlock_review.json")
        live_bridge_files = [
            p
            for p in _git_ls_files()
            if p.startswith("framework/") and Path(p).name.startswith("live_bridge_")
        ]
        self.assertGreater(
            len(live_bridge_files),
            0,
            "expected a real live_bridge surface under framework/ at baseline",
        )
        self.assertEqual(
            review["surface_observation"]["live_bridge_framework_file_count"],
            len(live_bridge_files),
        )

    def test_no_live_bridge_test_fixture_exists(self) -> None:
        lb_tests = [
            p
            for p in _git_ls_files()
            if p.startswith("tests/") and Path(p).name.startswith("test_live_bridge_")
        ]
        self.assertEqual(lb_tests, [])

    def test_no_live_bridge_case_in_offline_scenarios(self) -> None:
        path = REPO_ROOT / "tests" / "run_offline_scenarios.sh"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        self.assertNotIn("live_bridge", text)

    def test_unlock_criteria_live_bridge_row_is_unchanged(self) -> None:
        unlock = _load("tactical_unlock_criteria.json")
        lb = next(
            (f for f in unlock["families"] if f["family_id"] == "live_bridge"), None
        )
        self.assertIsNotNone(lb)
        assert lb is not None
        self.assertEqual(lb["unlock_state"], "locked")
        self.assertTrue(lb["review_packet_required"])
        self.assertEqual(lb["currently_met_preconditions"], [])
        self.assertEqual(
            lb.get("adr_ref"),
            "governance/authority_adr_0003_lob_w3_classification.md",
        )

    def test_family_classification_live_bridge_row_is_unchanged(self) -> None:
        classification = _load("tactical_family_classification.json")
        lb = next(
            (
                f
                for f in classification["families"]
                if f["family_id"] == "live_bridge"
            ),
            None,
        )
        self.assertIsNotNone(lb)
        assert lb is not None
        self.assertEqual(lb["current_classification"], "provisional_precursor")
        self.assertEqual(lb["canonical_phase_dependency"], 6)

    def test_runtime_adoption_report_live_bridge_row_is_zero_adoption(self) -> None:
        report = _load("runtime_adoption_report.json")
        lb = next(
            (
                r
                for r in report["tactical_family_adoption"]
                if r["family_id"] == "live_bridge"
            ),
            None,
        )
        self.assertIsNotNone(lb)
        assert lb is not None
        self.assertEqual(lb["adopting_files"], 0)
        self.assertEqual(lb["adopting_paths"], [])

    def test_phase_6_remains_open_and_unadvanced(self) -> None:
        roadmap = _load("canonical_roadmap.json")
        p6 = next((p for p in roadmap["phases"] if p["phase_id"] == 6), None)
        self.assertIsNotNone(p6)
        assert p6 is not None
        self.assertEqual(p6["status"], "open")

    def test_adr_0013_is_committed(self) -> None:
        self.assertTrue(
            (GOV_DIR / "authority_adr_0013_live_bridge_family_unlock_review.md").exists()
        )

    def test_adr_0003_lob_w3_pause_authority_still_present(self) -> None:
        adr_path = GOV_DIR / "authority_adr_0003_lob_w3_classification.md"
        self.assertTrue(adr_path.exists())
        review = _load("live_bridge_family_unlock_review.json")
        self.assertIn(
            "governance/authority_adr_0003_lob_w3_classification.md",
            review["evidence_inputs"],
        )
        self.assertTrue(review["invariants_preserved"]["lob_w3_pause_preserved"])

    def test_review_preserves_current_allowed_class(self) -> None:
        nextc = _load("next_package_class.json")
        self.assertIn(nextc["current_allowed_class"], {"ratification_only", "capability_session"})

    def test_review_preserves_phase2_closed_state(self) -> None:
        phase2 = _load("phase2_adoption_decision.json")
        self.assertEqual(phase2["decision"], "closed")


if __name__ == "__main__":
    unittest.main()
