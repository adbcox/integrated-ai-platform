"""Offline coverage for RECON-W2 Phase 0 closure."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"
CLOSER = REPO_ROOT / "bin" / "governance_phase0_closer.py"


def _load(name: str) -> dict:
    return json.loads((GOV_DIR / name).read_text(encoding="utf-8"))


def _live_schema_paths() -> list[str]:
    files = subprocess.check_output(
        ["git", "ls-files", "framework/*_schema.py"],
        cwd=REPO_ROOT,
        text=True,
    ).splitlines()
    return sorted(f for f in files if f)


class Phase0ClosureTest(unittest.TestCase):
    def test_registry_enumerates_every_framework_schema(self) -> None:
        payload = _load("schema_contract_registry.json")
        expected = _live_schema_paths()
        actual = sorted(entry["path"] for entry in payload["schemas"])
        self.assertEqual(actual, expected)

    def test_registry_totals_match_live_enumeration(self) -> None:
        payload = _load("schema_contract_registry.json")
        self.assertEqual(payload["total"], len(_live_schema_paths()))
        self.assertEqual(
            payload["active_count"] + payload["legacy_frozen_count"],
            payload["total"],
        )

    def test_every_schema_entry_has_classification_rationale_and_adr(self) -> None:
        payload = _load("schema_contract_registry.json")
        for entry in payload["schemas"]:
            self.assertIn(entry["classification"], {"active", "legacy_frozen"})
            self.assertTrue(entry["rationale"])
            self.assertTrue(entry["adr_ref"])

    def test_closure_decision_closed_requires_all_entries_resolved(self) -> None:
        decision = _load("phase0_closure_decision.json")
        registry = _load("schema_contract_registry.json")
        all_resolved = all(
            s["classification"] in {"active", "legacy_frozen"} and s.get("adr_ref")
            for s in registry["schemas"]
        )
        if all_resolved:
            self.assertEqual(decision["decision"], "closed")
        else:
            self.assertEqual(decision["decision"], "open")

    def test_closure_decision_records_baseline_commit(self) -> None:
        decision = _load("phase0_closure_decision.json")
        self.assertEqual(
            decision["baseline_commit"],
            "53ae4d4f177b176a7bffaa63988f63fa0efa622c",
        )
        self.assertEqual(decision["as_of_commit"], decision["baseline_commit"])

    def test_closer_check_is_idempotent(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLOSER), "--check", "--fail-on-diff"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            f"phase0 closer --check failed: {result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
