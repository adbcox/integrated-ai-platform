#!/usr/bin/env python3
"""LACE2-P6: Drive ReplayGate on bounded LACE2 enriched traces."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.replay_proof import ReplayProofRunner

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"


def main() -> None:
    runner = ReplayProofRunner()
    record = runner.run()
    path = runner.emit(record, ARTIFACT_DIR)
    print(f"proof_id:            {record.proof_id}")
    print(f"total_traces:        {record.total_traces}")
    print(f"replayable_count:    {record.replayable_count}")
    print(f"priority_dist:       {record.priority_distribution}")
    print(f"artifact:            {path}")


if __name__ == "__main__":
    main()
