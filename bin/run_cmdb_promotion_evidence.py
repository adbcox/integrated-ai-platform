#!/usr/bin/env python3
"""Run CMDB promotion evidence evaluation for LAPC1.

Usage: python3 bin/run_cmdb_promotion_evidence.py [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.cmdb_promotion_evidence import evaluate_cmdb_promotion_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate CMDB promotion evidence.")
    parser.add_argument("--artifact-dir", default="artifacts/cmdb_promotion_evidence")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = evaluate_cmdb_promotion_evidence(
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nOverall result: {report.overall_result}")
    print(f"Criteria passed: {report.criteria_passed}/{report.criteria_total}")
    print()
    print(f"{'Criterion':<40} {'Passed':<8} {'Observed'}")
    print("-" * 80)
    for cr in report.criterion_results:
        print(f"  {cr.criterion:<38} {str(cr.passed):<8} {cr.observed[:35]}")

    if not args.dry_run and report.artifact_path:
        print(f"\nArtifact: {report.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
