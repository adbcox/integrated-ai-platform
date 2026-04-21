#!/usr/bin/env python3
"""LACE1-P14: Demo retrieval enrichment substrate on a sample query."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.retrieval_enrichment_substrate import RetrievalEnrichmentSubstrate

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE1"

_SAMPLE_QUERY = ["improve", "ExecutorFactory", "scheduling", "WorkerRuntime"]
_SAMPLE_CANDIDATES = [
    "framework/code_executor.py",
    "framework/worker_runtime.py",
    "framework/scheduler.py",
    "framework/job_schema.py",
    "docs/roadmap/items/RM-GOV-001.yaml",
]
_SAMPLE_BASE_SCORES = {
    "framework/code_executor.py": 14.5,
    "framework/worker_runtime.py": 13.2,
    "framework/scheduler.py": 11.0,
    "framework/job_schema.py": 9.8,
    "docs/roadmap/items/RM-GOV-001.yaml": 7.3,
}


def main() -> None:
    substrate = RetrievalEnrichmentSubstrate()
    record = substrate.enrich(
        _SAMPLE_QUERY,
        _SAMPLE_CANDIDATES,
        base_scores=_SAMPLE_BASE_SCORES,
    )
    path = substrate.emit(record, ARTIFACT_DIR)

    print(f"record_id:      {record.record_id}")
    print(f"entity_names:   {record.entity_names}")
    print(f"artifact:       {path}")
    print("\nEnriched ranking:")
    for c in record.enriched_candidates:
        print(f"  {c.path}: base={c.base_score} + entity_boost={c.entity_boost} + domain={c.domain_bonus} = {c.enriched_score}")


if __name__ == "__main__":
    main()
