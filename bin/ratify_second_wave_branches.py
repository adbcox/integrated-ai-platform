#!/usr/bin/env python3
"""Ratify second-wave domain branches for LAPC1.

Usage: python3 bin/ratify_second_wave_branches.py [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.domain_branch_second_wave_ratifier import ratify_second_wave_promotion


def main() -> int:
    parser = argparse.ArgumentParser(description="Ratify second-wave domain branch promotions.")
    parser.add_argument("--artifact-dir", default="artifacts/second_wave_promotion")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    artifact = ratify_second_wave_promotion(
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nTotal branches: {artifact.total_branches}")
    print(f"Any done: {artifact.any_done}")
    print(f"All scaffold_complete: {artifact.all_scaffold_complete}")
    print()
    print(f"{'Branch':<28} {'Verdict':<40} {'Criteria'}")
    print("-" * 80)
    for r in artifact.records:
        print(f"  {r.branch_name:<26} {r.verdict:<40} {r.criteria_passed}/{r.criteria_total}")

    if not args.dry_run and artifact.artifact_path:
        print(f"\nArtifact: {artifact.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
