#!/usr/bin/env python3
"""Run Aider live execution gate for LAPC1.

Usage: python3 bin/run_aider_live_gate.py [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.aider_live_execution_gate import evaluate_aider_live_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Aider live execution gate.")
    parser.add_argument("--artifact-dir", default="artifacts/aider_live_gate")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = evaluate_aider_live_gate(
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nOverall result: {report.overall_result}")
    print(f"Live execution safe: {report.live_execution_safe}")
    if report.blocking_checks:
        print(f"Blocking checks: {report.blocking_checks}")
    print()
    print(f"{'Check':<30} {'Passed':<8} {'Observed'}")
    print("-" * 80)
    for c in report.checks:
        print(f"  {c.check_name:<28} {str(c.passed):<8} {c.observed_value[:40]}")

    if not args.dry_run and report.artifact_path:
        print(f"\nArtifact: {report.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
