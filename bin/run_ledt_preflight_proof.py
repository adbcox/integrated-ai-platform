#!/usr/bin/env python3
"""LEDT-P3: Prove local execution preflight on representative samples."""
from __future__ import annotations
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.local_exec_preflight import LocalExecPreflightEvaluator

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LEDT"

SAMPLES = [
    ("LEDT-P3-seam-test", 2, ["make check", "pytest tests/test_ledt_preflight_seam.py -v"]),
    ("LEDT-P4-route-decision", 3, ["make check", "pytest tests/test_ledt_exec_route_decision_seam.py -v"]),
    ("LEDT-P10-proof-harness", 1, ["make check", "pytest tests/test_ledt_local_first_proof_seam.py -v"]),
]


def main() -> None:
    ev = LocalExecPreflightEvaluator()
    reports = [ev.evaluate(pid, scope, cmds) for pid, scope, cmds in SAMPLES]
    path = ev.emit(reports, ARTIFACT_DIR)
    print(f"sample_count:   {len(reports)}")
    print(f"ready_count:    {sum(1 for r in reports if r.overall_ready)}")
    for r in reports:
        print(f"  {r.packet_id}: ready={r.overall_ready} risk={r.file_scope_risk}")
    print(f"artifact:       {path}")


if __name__ == "__main__":
    main()
