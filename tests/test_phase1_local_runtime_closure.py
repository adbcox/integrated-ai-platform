"""Offline closure-assertion coverage for PHASE-1-CLOSE-1."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"
EVIDENCE_PATH = GOV_DIR / "phase1_local_runtime_closure_evidence.json"
ADR_PATH = GOV_DIR / "authority_adr_0018_phase1_local_runtime_closure.md"


def _load(name: str) -> dict:
    return json.loads((GOV_DIR / name).read_text(encoding="utf-8"))


class Phase1LocalRuntimeClosureTest(unittest.TestCase):
    def test_closure_evidence_and_adr_exist(self) -> None:
        self.assertTrue(EVIDENCE_PATH.exists(), f"missing {EVIDENCE_PATH}")
        self.assertTrue(ADR_PATH.exists(), f"missing {ADR_PATH}")

    def test_evidence_records_expected_metadata(self) -> None:
        payload = _load("phase1_local_runtime_closure_evidence.json")
        self.assertEqual(payload["phase_id"], 1)
        self.assertEqual(payload["closure_package_id"], "PHASE-1-CLOSE-1")
        self.assertEqual(
            payload["closure_adr_ref"],
            "governance/authority_adr_0018_phase1_local_runtime_closure.md",
        )
        self.assertEqual(
            payload["phase_scope"],
            "local_runtime_hardening_for_ollama_first_execution",
        )

    def test_evidence_references_all_deliverables_on_disk(self) -> None:
        payload = _load("phase1_local_runtime_closure_evidence.json")
        deliverables = payload["deliverables"]
        referenced_paths: list[str] = []
        for entry in deliverables.values():
            for key, value in entry.items():
                if isinstance(value, str):
                    referenced_paths.append(value)
                elif isinstance(value, list):
                    referenced_paths.extend(value)
        self.assertGreater(len(referenced_paths), 0)
        for rel in referenced_paths:
            self.assertTrue(
                (REPO_ROOT / rel).exists(),
                f"deliverable path missing: {rel}",
            )

    def test_phase1_ratification_decision_still_closed(self) -> None:
        decision = _load("phase1_ratification_decision.json")
        self.assertEqual(decision["decision"], "closed")
        self.assertEqual(decision["phase_id"], 1)

    def test_closure_preserves_post_closure_invariants(self) -> None:
        nextc = _load("next_package_class.json")
        self.assertIn(nextc["current_allowed_class"], {"ratification_only", "capability_session"})
        phase2 = _load("phase2_adoption_decision.json")
        self.assertEqual(phase2["decision"], "closed")
        unlock = _load("tactical_unlock_criteria.json")
        for family in unlock["families"]:
            self.assertEqual(
                family["unlock_state"],
                "locked",
                f"family {family['family_id']!r} must remain locked",
            )

    def test_success_invariants_all_true(self) -> None:
        payload = _load("phase1_local_runtime_closure_evidence.json")
        for key, value in payload["success_invariants"].items():
            self.assertTrue(value, f"success invariant {key!r} must be true")


if __name__ == "__main__":
    unittest.main()
