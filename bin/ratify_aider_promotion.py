#!/usr/bin/env python3
"""Ratify Aider promotion for LAPC1.

Usage: python3 bin/ratify_aider_promotion.py [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.aider_live_execution_gate import evaluate_aider_live_gate
from framework.aider_live_proof import run_aider_live_proof
from framework.aider_promotion_ratifier import ratify_aider_promotion


def main() -> int:
    parser = argparse.ArgumentParser(description="Ratify Aider promotion decision.")
    parser.add_argument("--artifact-dir", default="artifacts/aider_promotion")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    gate = evaluate_aider_live_gate(dry_run=True)
    proof = run_aider_live_proof(gate, num_runs=3, dry_run=True)
    artifact = ratify_aider_promotion(
        gate,
        proof,
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nDecision: {artifact.decision}")
    print(f"Gate result: {artifact.gate_result}")
    print(f"Proof status: {artifact.proof_status}")
    print(f"Successful live runs: {artifact.successful_live_runs}")
    print(f"Live execution safe: {artifact.live_execution_safe}")
    print(f"\nRationale: {artifact.rationale}")

    if not args.dry_run and artifact.artifact_path:
        print(f"\nArtifact: {artifact.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
