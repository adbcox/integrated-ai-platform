#!/usr/bin/env python3
"""LACE2-P5: Enrich LACE2 proof-flow traces via ExecutionTraceEnricher."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.trace_enrichment_proof import TraceEnrichmentProofRunner

ARTIFACT_DIR = REPO_ROOT / "artifacts" / "expansion" / "LACE2"


def main() -> None:
    runner = TraceEnrichmentProofRunner()
    record = runner.run()
    path = runner.emit(record, ARTIFACT_DIR)
    print(f"proof_id:              {record.proof_id}")
    print(f"input_trace_count:     {record.input_trace_count}")
    print(f"outcome_distribution:  {record.outcome_class_distribution}")
    print(f"artifact:              {path}")


if __name__ == "__main__":
    main()
