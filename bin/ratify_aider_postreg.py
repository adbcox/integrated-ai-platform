#!/usr/bin/env python3
"""Reratify Aider promotion after AGCC1 command registration.

Usage: python3 bin/ratify_aider_postreg.py [--num-runs N] [--dry-run]
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
    parser = argparse.ArgumentParser(description="Reratify Aider promotion post-registration.")
    parser.add_argument("--num-runs", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    gate = evaluate_aider_live_gate(dry_run=args.dry_run)
    proof = run_aider_live_proof(gate, num_runs=args.num_runs, dry_run=args.dry_run)
    artifact = ratify_aider_promotion(gate, proof, dry_run=args.dry_run)

    print(f"\n=== Aider Post-Registration Ratification ===")
    print(f"  decision:            {artifact.decision}")
    print(f"  gate_result:         {artifact.gate_result}")
    print(f"  proof_status:        {artifact.proof_status}")
    print(f"  successful_live_runs:{artifact.successful_live_runs}")
    print(f"  live_execution_safe: {artifact.live_execution_safe}")
    print(f"  rationale:           {artifact.rationale}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
