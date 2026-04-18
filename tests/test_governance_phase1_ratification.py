"""Offline coverage for RECON-W2 Phase 1 ratification."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GOV_DIR = REPO_ROOT / "governance"
RATIFIER = REPO_ROOT / "bin" / "governance_phase1_ratifier.py"


def _load(name: str) -> dict:
    return json.loads((GOV_DIR / name).read_text(encoding="utf-8"))


class Phase1RatificationTest(unittest.TestCase):
    def test_callgraph_self_adoption_is_complete(self) -> None:
        payload = _load("runtime_primitive_callgraph.json")
        self.assertTrue(payload["self_adoption_complete"])

    def test_required_worker_runtime_edges_present(self) -> None:
        payload = _load("runtime_primitive_callgraph.json")
        worker_imports = {
            e["to"]
            for e in payload["edges"]
            if e["from"] == "worker_runtime" and e["kind"] == "import"
        }
        for target in ("tool_system", "permission_engine", "sandbox", "workspace"):
            self.assertIn(target, worker_imports)

    def test_phase1_decision_is_closed(self) -> None:
        decision = _load("phase1_ratification_decision.json")
        self.assertEqual(decision["decision"], "closed")

    def test_ratified_contract_version_is_present(self) -> None:
        decision = _load("phase1_ratification_decision.json")
        self.assertIn("ratified_contract_version", decision)
        self.assertTrue(decision["ratified_contract_version"])
        self.assertTrue(decision["ratified_contract_version"].startswith("rt-"))

    def test_phase1_records_baseline_commit(self) -> None:
        decision = _load("phase1_ratification_decision.json")
        self.assertEqual(
            decision["baseline_commit"],
            "53ae4d4f177b176a7bffaa63988f63fa0efa622c",
        )

    def test_ratifier_check_is_idempotent(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RATIFIER), "--check", "--fail-on-diff"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            f"phase1 ratifier --check failed: {result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
