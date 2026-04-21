#!/usr/bin/env python3
"""LACE2-P4: Drive RepairPolicyGate across six bounded failure scenarios."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.repair_policy_proof import RepairPolicyProofRunner

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"


def main() -> None:
    runner = RepairPolicyProofRunner()
    record = runner.run()
    path = runner.emit(record, ARTIFACT_DIR)
    print(f"proof_id:           {record.proof_id}")
    print(f"rows_total:         {record.rows_total}")
    print(f"rows_correct:       {record.rows_correct}")
    print(f"decision_accuracy:  {record.decision_accuracy:.3f}")
    print(f"artifact:           {path}")
    print("\nDecision table:")
    for r in record.rows:
        ok = "OK" if r.matches_expected else "MISMATCH"
        print(f"  {r.row_id}: expected={r.expected_action}, actual={r.actual_action} [{ok}]")


if __name__ == "__main__":
    main()
