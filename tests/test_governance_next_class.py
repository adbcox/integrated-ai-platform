"""Offline coverage for RECON-W2 next-allowed-class authority."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"


def _load(name: str) -> dict:
    return json.loads((GOV_DIR / name).read_text(encoding="utf-8"))


class NextClassTest(unittest.TestCase):
    def test_current_allowed_class_is_ratification_only(self) -> None:
        payload = _load("next_package_class.json")
        self.assertEqual(payload["current_allowed_class"], "ratification_only")

    def test_capability_session_transition_gated_on_phase2_closure(self) -> None:
        payload = _load("next_package_class.json")
        cap = next(
            (t for t in payload["transitions"] if t["to"] == "capability_session"),
            None,
        )
        self.assertIsNotNone(cap, "capability_session transition missing")
        assert cap is not None
        self.assertIn("Phase 2", cap["gate"])
        self.assertIn("closed", cap["blocked_until"])

    def test_no_transition_directly_authorizes_tactical_expansion(self) -> None:
        payload = _load("next_package_class.json")
        forbidden = {"tactical_expansion", "feature_expansion"}
        for transition in payload["transitions"]:
            self.assertNotIn(
                transition["to"],
                forbidden,
                f"transition to {transition['to']!r} is forbidden in this packet",
            )

    def test_tactical_review_transition_requires_per_family_unlock(self) -> None:
        payload = _load("next_package_class.json")
        tactical = next(
            (t for t in payload["transitions"] if t["to"] == "tactical_review"),
            None,
        )
        self.assertIsNotNone(tactical, "tactical_review transition missing")
        assert tactical is not None
        self.assertIn("per-family", tactical["gate"])

    def test_decision_files_reflect_post_recon_w2_state(self) -> None:
        phase0 = _load("phase0_closure_decision.json")
        phase1 = _load("phase1_ratification_decision.json")
        phase2 = _load("phase2_adoption_decision.json")
        nextc = _load("next_package_class.json")
        self.assertEqual(phase0["phase_id"], 0)
        self.assertEqual(phase0["decision"], "closed")
        self.assertEqual(phase1["phase_id"], 1)
        self.assertEqual(phase1["decision"], "closed")
        self.assertEqual(phase2["phase_id"], 2)
        self.assertEqual(phase2["decision"], "adopted_partial")
        self.assertEqual(nextc["current_allowed_class"], "ratification_only")


if __name__ == "__main__":
    unittest.main()
