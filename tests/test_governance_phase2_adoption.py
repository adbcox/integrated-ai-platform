"""Offline coverage for RECON-W2 Phase 2 adoption state."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"
EXTRACTOR = REPO_ROOT / "bin" / "governance_phase2_extractor.py"


def _load(name: str) -> dict:
    return json.loads((GOV_DIR / name).read_text(encoding="utf-8"))


class Phase2AdoptionTest(unittest.TestCase):
    def test_inner_loop_contract_has_at_least_one_failure_class(self) -> None:
        payload = _load("inner_loop_contract.json")
        self.assertGreaterEqual(len(payload["failure_classes"]), 1)

    def test_inner_loop_contract_has_at_least_one_trace_kind(self) -> None:
        payload = _load("inner_loop_contract.json")
        self.assertGreaterEqual(len(payload["trace_kinds_emitted"]), 1)

    def test_phase2_decision_is_adopted_partial(self) -> None:
        decision = _load("phase2_adoption_decision.json")
        self.assertEqual(decision["decision"], "adopted_partial")

    def test_phase2_decision_never_closed_in_recon_w2(self) -> None:
        decision = _load("phase2_adoption_decision.json")
        self.assertNotEqual(
            decision["decision"],
            "closed",
            "RECON-W2 must not set Phase 2 decision to closed",
        )

    def test_phase2_records_baseline_commit(self) -> None:
        decision = _load("phase2_adoption_decision.json")
        self.assertEqual(
            decision["baseline_commit"],
            "53ae4d4f177b176a7bffaa63988f63fa0efa622c",
        )

    def test_inner_loop_contract_lists_required_keys(self) -> None:
        payload = _load("inner_loop_contract.json")
        for key in (
            "max_cycles_source",
            "setup_command_semantics",
            "validate_command_semantics",
            "repair_edits_shape",
            "snapshot_restore_triggers",
            "failure_classes",
            "retryable_failure_classes",
            "trace_kinds_emitted",
        ):
            self.assertIn(key, payload)

    def test_extractor_check_is_idempotent(self) -> None:
        result = subprocess.run(
            [sys.executable, str(EXTRACTOR), "--check", "--fail-on-diff"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            f"phase2 extractor --check failed: {result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
