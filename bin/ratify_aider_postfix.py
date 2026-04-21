#!/usr/bin/env python3
"""Reratify Aider promotion using wired gate and proof from APCC1.

Usage: python3 bin/ratify_aider_postfix.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.aider_live_gate_wired import evaluate_wired_aider_gate, run_wired_aider_proof
from framework.aider_promotion_ratifier import ratify_aider_promotion


def main() -> int:
    parser = argparse.ArgumentParser(description="Reratify Aider promotion post-fix.")
    parser.add_argument("--num-runs", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    gate = evaluate_wired_aider_gate(dry_run=args.dry_run)
    proof = run_wired_aider_proof(gate, num_runs=args.num_runs, dry_run=args.dry_run)
    artifact = ratify_aider_promotion(gate, proof, dry_run=args.dry_run)

    print("\n=== Aider Post-Fix Ratification ===")
    print(f"  decision:            {artifact.decision}")
    print(f"  gate_result:         {artifact.gate_result}")
    print(f"  proof_status:        {artifact.proof_status}")
    print(f"  successful_runs:     {artifact.successful_live_runs}")
    print(f"  live_execution_safe: {artifact.live_execution_safe}")
    print(f"  rationale:           {artifact.rationale}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
