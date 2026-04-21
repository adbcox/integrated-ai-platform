#!/usr/bin/env python3
"""LEDT-P2: Prove local execution eligibility contract on representative samples."""
from __future__ import annotations
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.local_exec_eligibility_contract import (
    LocalExecEligibilityEvaluator, LocalExecEligibilityInput,
)

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LEDT"

SAMPLES = [
    LocalExecEligibilityInput("LEDT-P2-seam-test", 2, False, False, False,
                               ["make check", "pytest tests/test_ledt_eligibility_contract_seam.py -v"]),
    LocalExecEligibilityInput("LEDT-P4-route-decision", 3, False, False, False,
                               ["make check", "pytest tests/test_ledt_exec_route_decision_seam.py -v"]),
    LocalExecEligibilityInput("hypothetical-cloud-integration", 12, True, False, False,
                               ["make check"]),
    LocalExecEligibilityInput("hypothetical-scheduler-redesign", 2, False, True, False,
                               ["make check"]),
]


def main() -> None:
    evaluator = LocalExecEligibilityEvaluator()
    records = [evaluator.evaluate(s) for s in SAMPLES]
    path = evaluator.emit(records, ARTIFACT_DIR)
    eligible = sum(1 for r in records if r.eligible)
    print(f"sample_count:      {len(records)}")
    print(f"eligible_count:    {eligible}")
    print(f"disqualified:      {len(records) - eligible}")
    for r in records:
        mark = "OK" if r.eligible else f"DISQ:{r.disqualifiers[0][:40]}"
        print(f"  {r.packet_id[:40]}: {mark}")
    print(f"artifact:          {path}")


if __name__ == "__main__":
    main()
