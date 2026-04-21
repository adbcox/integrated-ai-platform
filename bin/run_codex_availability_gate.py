#!/usr/bin/env python3
"""Run Codex availability gate for LAPC1.

Usage: python3 bin/run_codex_availability_gate.py [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.codex_availability_gate import evaluate_codex_availability


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Codex availability gate.")
    parser.add_argument("--artifact-dir", default="artifacts/codex_availability")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = evaluate_codex_availability(
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nOverall result: {report.overall_result}")
    print(f"Codex available: {report.codex_available}")
    print(f"Policy allows execution: {report.policy_allows_execution}")
    if report.blocking_reason:
        print(f"Blocking reason: {report.blocking_reason}")
    print()
    print(f"{'Check':<35} {'Passed':<8} {'Observed'}")
    print("-" * 75)
    for c in report.checks:
        print(f"  {c.check_name:<33} {str(c.passed):<8} {c.observed_value}")

    if not args.dry_run and report.artifact_path:
        print(f"\nArtifact: {report.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
