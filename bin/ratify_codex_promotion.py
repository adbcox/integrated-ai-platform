#!/usr/bin/env python3
"""Ratify Codex promotion for LAPC1.

Usage: python3 bin/ratify_codex_promotion.py [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.codex_availability_gate import evaluate_codex_availability
from framework.codex_promotion_ratifier import ratify_codex_promotion


def main() -> int:
    parser = argparse.ArgumentParser(description="Ratify Codex promotion decision.")
    parser.add_argument("--artifact-dir", default="artifacts/codex_promotion")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    avail = evaluate_codex_availability(dry_run=True)
    artifact = ratify_codex_promotion(
        avail,
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nDecision: {artifact.decision}")
    print(f"Availability result: {artifact.availability_result}")
    print(f"Codex available: {artifact.codex_available}")
    if artifact.defer_reason:
        print(f"Defer reason: {artifact.defer_reason}")
    print(f"Next review trigger: {artifact.next_review_trigger}")
    print(f"\nRationale: {artifact.rationale}")

    if not args.dry_run and artifact.artifact_path:
        print(f"\nArtifact: {artifact.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
