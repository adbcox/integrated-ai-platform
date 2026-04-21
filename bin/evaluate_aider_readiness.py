#!/usr/bin/env python3
"""Aider readiness evaluator.

Usage: python3 bin/evaluate_aider_readiness.py [--artifact-dir PATH] [--dry-run]

Evaluates Aider readiness criteria from live evidence. Prints criterion table and verdict.
Exits 0 always.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.readiness_evaluator import evaluate_readiness


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate Aider adapter readiness.")
    parser.add_argument("--artifact-dir", default="artifacts/readiness")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    evaluation = evaluate_readiness(
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\n{'CRITERION':<30} {'OBSERVED':>10} {'THRESHOLD':>10} {'STATUS':>8}")
    print("-" * 62)
    for c in evaluation.criteria:
        status = "PASS" if c.passed else "FAIL"
        print(
            f"{c.name:<30} "
            f"{c.observed_value:>10.4f} "
            f"{c.threshold:>10.4f} "
            f"{status:>8}"
        )
    print("-" * 62)
    print()
    print(f"Verdict: {evaluation.readiness_verdict}")
    if evaluation.defer_reasons:
        print("Defer reasons:")
        for r in evaluation.defer_reasons:
            print(f"  - {r}")
    print()

    if not args.dry_run and evaluation.artifact_path:
        print(f"Artifact: {evaluation.artifact_path}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
