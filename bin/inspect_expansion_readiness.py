#!/usr/bin/env python3
"""Inspect expansion readiness for LAEC1.

Usage: python3 bin/inspect_expansion_readiness.py [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.expansion_readiness_inspector import inspect_expansion_readiness


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect LAEC1 expansion readiness.")
    parser.add_argument("--artifact-dir", default="artifacts/expansion_readiness")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    report = inspect_expansion_readiness(
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nOverall status: {report.overall_status}")
    print(f"Inspected at:  {report.inspected_at}")
    print()
    print("Item table:")
    for item in report.items:
        print(f"  [{item.status.upper():8s}] {item.name}: {item.detail}")
    print()

    if not args.dry_run and report.artifact_path:
        print(f"Artifact: {report.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
