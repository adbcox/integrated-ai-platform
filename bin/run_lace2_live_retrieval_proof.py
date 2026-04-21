#!/usr/bin/env python3
"""LACE2-P2: Run live retrieval wiring proof."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.live_retrieval_proof import LiveRetrievalProofRunner

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"


def main() -> None:
    runner = LiveRetrievalProofRunner(REPO_ROOT)
    record = runner.run(
        "add guard clause to ExecutorFactory scheduling loop in WorkerRuntime",
        max_files=200,
        top_n=8,
    )
    path = runner.emit(record, ARTIFACT_DIR)
    print(f"proof_id:             {record.proof_id}")
    print(f"total_files_scanned:  {record.total_files_scanned}")
    print(f"total_symbols:        {record.total_symbols}")
    print(f"entity_names:         {record.entity_names}")
    print(f"top_candidates:       {record.top_candidate_paths[:3]}")
    print(f"enriched_top:         {record.enriched_top_paths[:3]}")
    print(f"artifact:             {path}")


if __name__ == "__main__":
    main()
