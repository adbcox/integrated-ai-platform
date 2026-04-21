#!/usr/bin/env python3
"""LACE2-P3: Run decomp-to-handoff proof on real repo target files."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.decomp_handoff_proof import DecompHandoffProofRunner

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"

_CANDIDATE_FILES = [
    "framework/scheduler.py",
    "framework/worker_runtime.py",
    "framework/job_schema.py",
]
_DESCRIPTION = "add guard clause to prevent null job submission in scheduler and worker runtime"


def main() -> None:
    target_files = [f for f in _CANDIDATE_FILES if (REPO_ROOT / f).exists()]
    if not target_files:
        print("ERROR: no target files found", file=sys.stderr)
        sys.exit(1)

    runner = DecompHandoffProofRunner()
    record = runner.run(_DESCRIPTION, target_files)
    path = runner.emit(record, ARTIFACT_DIR)

    print(f"proof_id:         {record.proof_id}")
    print(f"target_files:     {record.target_files}")
    print(f"subtask_count:    {record.subtask_count}")
    print(f"subtask_kinds:    {record.subtask_kinds}")
    print(f"total_orders:     {record.total_orders}")
    print(f"handoff_policy:   {record.handoff_policy}")
    print(f"artifact:         {path}")


if __name__ == "__main__":
    main()
