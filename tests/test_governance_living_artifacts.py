"""Offline coverage for RECON-W2C living generator-owned artifact classification.

Asserts the invariants declared by ADR 0009 and the machine-readable
acceptance record in ``governance/living_generator_artifacts.json``.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"
LIVING_PATH = GOV_DIR / "living_generator_artifacts.json"
ADR_PATH = GOV_DIR / "authority_adr_0009_living_generator_artifacts.md"

EXPECTED_LIVING_PATHS = {
    "governance/schema_contract_registry.json",
    "governance/runtime_contract_version.json",
    "governance/runtime_adoption_report.json",
}

EXPECTED_ACCEPTED_COMMITS = {
    "0981c22b17a87d3e6548c0b337a40305c068c3d3",
    "864945ce43edd5f9bd7385eeb26740eabe94d969",
}


def _load(name: str) -> dict:
    return json.loads((GOV_DIR / name).read_text(encoding="utf-8"))


class LivingGeneratorArtifactsTest(unittest.TestCase):
    def test_living_generator_artifacts_exists(self) -> None:
        self.assertTrue(LIVING_PATH.exists(), f"missing {LIVING_PATH}")

    def test_adr_0009_exists(self) -> None:
        self.assertTrue(ADR_PATH.exists(), f"missing {ADR_PATH}")

    def test_lists_exactly_three_living_artifacts(self) -> None:
        payload = _load("living_generator_artifacts.json")
        paths = {entry["path"] for entry in payload["living_artifacts"]}
        self.assertEqual(paths, EXPECTED_LIVING_PATHS)

    def test_each_living_artifact_has_owner_generator_that_exists(self) -> None:
        payload = _load("living_generator_artifacts.json")
        for entry in payload["living_artifacts"]:
            self.assertEqual(entry["classification"], "living_generator_owned")
            owner = entry["owner_generator"]
            self.assertTrue(
                (REPO_ROOT / owner).exists(),
                f"owner generator missing: {owner}",
            )

    def test_accepted_commits_include_both(self) -> None:
        payload = _load("living_generator_artifacts.json")
        self.assertTrue(
            EXPECTED_ACCEPTED_COMMITS.issubset(set(payload["accepted_commits"])),
            f"accepted_commits={payload['accepted_commits']!r} must include "
            f"{EXPECTED_ACCEPTED_COMMITS!r}",
        )

    def test_accepted_state_preserves_post_closure_invariants(self) -> None:
        payload = _load("living_generator_artifacts.json")
        state = payload["accepted_state"]
        self.assertEqual(state["phase2_status"], "closed_ratified")
        self.assertEqual(state["current_allowed_class"], "ratification_only")
        self.assertIs(state["tactical_families_locked"], True)
        self.assertIs(state["lob_w3_paused_under_adr_0003"], True)

    def test_invariants_record_phase0_invariance_and_phase2_adr(self) -> None:
        payload = _load("living_generator_artifacts.json")
        invariants = payload["invariants"]
        self.assertIs(
            invariants["phase0_closure_invariant_under_consumer_drift"], True
        )
        self.assertEqual(
            invariants["phase2_closure_authority_adr"],
            "governance/authority_adr_0008_phase2_closure.md",
        )
        self.assertIs(invariants["machine_acceptance_recorded_here"], True)

    def test_governance_check_passes(self) -> None:
        result = subprocess.run(
            ["make", "governance-check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"make governance-check failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}",
        )

    def test_governance_ratify_passes(self) -> None:
        result = subprocess.run(
            ["make", "governance-ratify"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"make governance-ratify failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}",
        )

    def test_phase0_remains_closed(self) -> None:
        payload = _load("phase0_closure_decision.json")
        self.assertEqual(payload["decision"], "closed")

    def test_phase2_remains_closed(self) -> None:
        payload = _load("phase2_adoption_decision.json")
        self.assertEqual(payload["decision"], "closed")

    def test_current_allowed_class_ratification_only(self) -> None:
        payload = _load("next_package_class.json")
        self.assertIn(
            payload["current_allowed_class"],
            {"ratification_only", "capability_session"},
        )

    def test_every_tactical_family_remains_locked(self) -> None:
        payload = _load("tactical_unlock_criteria.json")
        for family in payload["families"]:
            self.assertEqual(
                family["unlock_state"],
                "locked",
                f"family {family.get('family_id')!r} is not locked",
            )


if __name__ == "__main__":
    unittest.main()
