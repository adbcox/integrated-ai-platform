#!/usr/bin/env python3
"""Run Aider live proof for LAPC1.

Usage: python3 bin/run_aider_live_proof.py [--num-runs N] [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.aider_live_execution_gate import evaluate_aider_live_gate
from framework.aider_live_proof import run_aider_live_proof


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bounded Aider live proof attempts.")
    parser.add_argument("--num-runs", type=int, default=3)
    parser.add_argument("--artifact-dir", default="artifacts/aider_live_proof")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    gate = evaluate_aider_live_gate(dry_run=True)
    print(f"\nGate result: {gate.overall_result} (live_execution_safe={gate.live_execution_safe})")
    if gate.blocking_checks:
        print(f"Blocking: {gate.blocking_checks}")

    report = run_aider_live_proof(
        gate,
        num_runs=args.num_runs,
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nProof status: {report.proof_status}")
    print(f"Successful runs: {report.successful_runs}/{report.total_runs}")
    print()
    print(f"{'Run':<5} {'Model':<32} {'Live':<6} {'OK':<6} {'Exit'}")
    print("-" * 70)
    for rec in report.records:
        print(f"  {rec.run_index:<3} {rec.model:<32} {str(rec.attempted_live):<6} {str(rec.success):<6} {rec.exit_code}")

    print(f"\nNotes: {report.notes}")

    if not args.dry_run and report.artifact_path:
        print(f"\nArtifact: {report.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
