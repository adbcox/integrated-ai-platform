#!/usr/bin/env python3
"""Evidence accumulation batch runner.

Usage: python3 bin/run_evidence_accumulation_batch.py [--runs-per-kind N] [--dry-run] [--artifact-dir PATH]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.evidence_accumulation_batch import BatchRunConfig, EvidenceAccumulationBatch


def main() -> int:
    parser = argparse.ArgumentParser(description="Run evidence accumulation batch.")
    parser.add_argument("--runs-per-kind", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--artifact-dir", default=None)
    args = parser.parse_args()

    config = BatchRunConfig(
        runs_per_kind=args.runs_per_kind,
        dry_run=args.dry_run,
        artifact_dir=Path(args.artifact_dir) if args.artifact_dir else None,
    )

    batch = EvidenceAccumulationBatch()
    result = batch.run(config)

    print(f"\nBatch run summary (dry_run={config.dry_run}):")
    print(f"  Total kinds: {result.total_kinds}")
    print(f"  Total runs: {result.total_runs}")
    print(f"  Successes: {result.total_successes}")
    print(f"  Failures: {result.total_failures}")
    print()
    for kr in result.kind_results:
        status = f"ok (s={kr.success_count}/f={kr.failure_count})"
        if kr.error:
            status = f"ERROR: {kr.error}"
        print(f"  {kr.task_kind}: {status}")
    print()

    if not config.dry_run and result.artifact_path:
        print(f"Artifact: {result.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
