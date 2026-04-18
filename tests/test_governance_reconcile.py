"""Offline coverage for RECON-W1 governance authority.

Runs under the stdlib unittest runner so the repo does not require pytest to
validate governance artifacts. pytest, if installed, will also discover these
TestCase classes.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"
RECONCILER = REPO_ROOT / "bin" / "governance_reconcile.py"

REQUIRED_METADATA_KEYS = (
    "schema_version",
    "authority_owner",
    "generated_at",
    "supersedes",
)

CANONICAL_ARTIFACTS = (
    "canonical_roadmap.json",
    "current_phase.json",
    "runtime_contract_version.json",
    "phase_gate_status.json",
    "runtime_adoption_report.json",
    "tactical_family_classification.json",
)

REQUIRED_FAMILIES = {"eo", "ed", "mc", "live_bridge", "ort", "pgs"}


def _load(name: str) -> dict:
    path = GOV_DIR / name
    if not path.exists():
        raise AssertionError(f"missing governance artifact: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


class GovernanceArtifactsTest(unittest.TestCase):
    def test_all_json_artifacts_have_required_metadata(self) -> None:
        for name in CANONICAL_ARTIFACTS:
            payload = _load(name)
            for key in REQUIRED_METADATA_KEYS:
                self.assertIn(key, payload, f"{name} missing metadata key {key!r}")

    def test_canonical_roadmap_covers_only_phases_0_through_6(self) -> None:
        payload = _load("canonical_roadmap.json")
        ids = sorted(entry["phase_id"] for entry in payload["phases"])
        self.assertEqual(ids, list(range(0, 7)))

    def test_no_canonical_phase_7_or_8(self) -> None:
        payload = _load("canonical_roadmap.json")
        present = {entry["phase_id"] for entry in payload["phases"]}
        self.assertFalse(present & {7, 8})

    def test_tactical_family_classification_covers_required_families(self) -> None:
        payload = _load("tactical_family_classification.json")
        fids = {entry["family_id"] for entry in payload["families"]}
        self.assertTrue(
            REQUIRED_FAMILIES.issubset(fids),
            f"missing tactical families: {REQUIRED_FAMILIES - fids}",
        )

    def test_current_phase_next_allowed_package_class_is_reconciliation_only(self) -> None:
        payload = _load("current_phase.json")
        self.assertEqual(payload["next_allowed_package_class"], "reconciliation_only")

    def test_current_phase_records_as_of_commit(self) -> None:
        payload = _load("current_phase.json")
        self.assertIn("as_of_commit", payload)
        self.assertIsInstance(payload["as_of_commit"], str)
        self.assertTrue(payload["as_of_commit"])

    def test_lob_family_classification_matches_adr_0003(self) -> None:
        payload = _load("tactical_family_classification.json")
        lob = next(
            (e for e in payload["families"] if e["family_id"] == "live_bridge"),
            None,
        )
        self.assertIsNotNone(lob, "live_bridge family missing")
        assert lob is not None  # for type checkers
        self.assertEqual(lob["current_classification"], "provisional_precursor")
        self.assertTrue(
            "ADR 0003" in lob["notes"] or "0003" in lob["notes"],
            "live_bridge classification notes must reference ADR 0003",
        )

    def test_tactical_families_are_not_canonical_phases(self) -> None:
        roadmap = _load("canonical_roadmap.json")
        for entry in roadmap["phases"]:
            self.assertNotIn(
                entry["phase_name"],
                REQUIRED_FAMILIES,
                f"tactical family {entry['phase_name']!r} appears as canonical phase",
            )

    def test_adrs_exist(self) -> None:
        for name in (
            "authority_adr_0001_source_of_truth.md",
            "authority_adr_0002_tactical_family_classification.md",
            "authority_adr_0003_lob_w3_classification.md",
        ):
            self.assertTrue((GOV_DIR / name).exists(), f"missing ADR: {name}")

    def test_governance_readme_exists(self) -> None:
        self.assertTrue((GOV_DIR / "README.md").exists())

    def test_reconciler_check_passes_on_freshly_written_state(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RECONCILER), "--check", "--fail-on-diff"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"governance_reconcile --check failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
