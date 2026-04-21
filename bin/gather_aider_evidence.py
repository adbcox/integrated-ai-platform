#!/usr/bin/env python3
"""Gather Aider adapter dry-run evidence for LAEC1.

Usage: python3 bin/gather_aider_evidence.py [--dry-run] [--num-runs N] [--artifact-dir PATH]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.aider_adapter_evidence import gather_aider_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Gather Aider adapter evidence.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--num-runs", type=int, default=3)
    parser.add_argument("--artifact-dir", default="artifacts/aider_evidence")
    args = parser.parse_args()

    report = gather_aider_evidence(
        num_runs=args.num_runs,
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nOverall status: {report.overall_status}")
    print(f"Total runs:     {report.total_runs}")
    print(f"Successful:     {report.successful_runs}")
    print(f"Failed:         {report.failed_runs}")
    print(f"Notes:          {report.notes}")
    print()
    print("Records:")
    for rec in report.records:
        status = "OK" if rec.success else "FAIL"
        print(f"  [{status}] run={rec.request_index} model={rec.model} kind={rec.task_kind}")

    if not args.dry_run and report.artifact_path:
        print(f"\nArtifact: {report.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
