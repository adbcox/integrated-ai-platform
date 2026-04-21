#!/usr/bin/env python3
"""Run wired Aider gate and proof post-fix for APCC1-P4.

Usage: python3 bin/run_aider_postfix_gate_proof.py [--dry-run] [--num-runs N]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.aider_live_gate_wired import evaluate_wired_aider_gate, run_wired_aider_proof


def main() -> int:
    parser = argparse.ArgumentParser(description="Wired Aider gate+proof post-fix.")
    parser.add_argument("--num-runs", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    gate = evaluate_wired_aider_gate(dry_run=args.dry_run)
    proof = run_wired_aider_proof(gate, num_runs=args.num_runs, dry_run=args.dry_run)

    print("\n=== Wired Aider Gate (Post-Fix) ===")
    print(f"  overall_result:      {gate.overall_result}")
    print(f"  live_execution_safe: {gate.live_execution_safe}")
    print(f"  blocking_checks:     {list(gate.blocking_checks)}")
    print()
    for c in gate.checks:
        status = "PASS" if c.passed else "FAIL"
        print(f"  [{status}] {c.check_name}: {c.detail or 'ok'}")

    print("\n=== Wired Aider Proof (Post-Fix) ===")
    print(f"  proof_status:    {proof.proof_status}")
    print(f"  successful_runs: {proof.successful_runs}/{proof.total_runs}")
    if proof.notes:
        print(f"  notes:           {proof.notes}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
