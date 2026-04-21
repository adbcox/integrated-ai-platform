#!/usr/bin/env python3
"""Ratify CMDB promotion for LAPC1.

Usage: python3 bin/ratify_cmdb_promotion.py [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.cmdb_promotion_evidence import evaluate_cmdb_promotion_evidence
from framework.cmdb_promotion_ratifier import ratify_cmdb_promotion


def main() -> int:
    parser = argparse.ArgumentParser(description="Ratify CMDB promotion decision.")
    parser.add_argument("--artifact-dir", default="artifacts/cmdb_promotion")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    evidence = evaluate_cmdb_promotion_evidence(dry_run=True)
    artifact = ratify_cmdb_promotion(
        evidence,
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nDecision: {artifact.decision}")
    print(f"Criteria passed: {artifact.criteria_passed}/{artifact.criteria_total}")
    print(f"Evidence result: {artifact.evidence_result}")
    print(f"\nRationale: {artifact.rationale}")

    if not args.dry_run and artifact.artifact_path:
        print(f"\nArtifact: {artifact.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
