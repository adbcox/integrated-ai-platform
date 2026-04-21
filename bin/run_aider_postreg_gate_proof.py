#!/usr/bin/env python3
"""Rerun Aider live gate and bounded live proof after AGCC1 command registration.

Usage: python3 bin/run_aider_postreg_gate_proof.py [--num-runs N] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.aider_live_execution_gate import evaluate_aider_live_gate
from framework.aider_live_proof import run_aider_live_proof


def main() -> int:
    parser = argparse.ArgumentParser(description="Rerun Aider gate and proof post-registration.")
    parser.add_argument("--num-runs", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    gate = evaluate_aider_live_gate(dry_run=args.dry_run)
    proof = run_aider_live_proof(gate, num_runs=args.num_runs, dry_run=args.dry_run)

    print(f"\n=== Post-Registration Gate ===")
    print(f"  overall_result:      {gate.overall_result}")
    print(f"  live_execution_safe: {gate.live_execution_safe}")
    print(f"  blocking_checks:     {gate.blocking_checks}")
    print()
    print(f"=== Post-Registration Proof ===")
    print(f"  proof_status:        {proof.proof_status}")
    print(f"  total_runs:          {proof.total_runs}")
    print(f"  successful_runs:     {proof.successful_runs}")
    print(f"  notes:               {proof.notes}")
    print()
    print(f"{'Run':<6} {'Attempted Live':<16} {'Dry Run':<10} {'Success':<10} {'Exit'}")
    print("-" * 60)
    for r in proof.records:
        print(f"  {r.run_index:<4} {str(r.attempted_live):<16} {str(r.dry_run_used):<10} {str(r.success):<10} {r.exit_code}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
