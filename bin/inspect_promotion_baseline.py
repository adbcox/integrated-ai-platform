#!/usr/bin/env python3
"""Inspect promotion baseline for LAPC1.

Usage: python3 bin/inspect_promotion_baseline.py [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.promotion_baseline_inspector import inspect_promotion_baseline


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect LAPC1 promotion baseline.")
    parser.add_argument("--artifact-dir", default="artifacts/promotion_baseline")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = inspect_promotion_baseline(
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nTotal candidates: {report.total_candidates}")
    print(f"Hard blocked: {report.hard_blocked_count}")
    print(f"Soft blocked: {report.soft_blocked_count}")
    print(f"Unblocked: {report.unblocked_count}")
    print()
    print(f"{'Candidate':<25} {'State':<16} {'Blocker':<8} {'Target'}")
    print("-" * 80)
    for c in report.candidates:
        print(f"  {c.name:<23} {c.current_state:<16} {c.blocker_class:<8} {c.promotion_target}")

    if not args.dry_run and report.artifact_path:
        print(f"\nArtifact: {report.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
