#!/usr/bin/env python3
"""Ratify terminal promotion for LAPC1.

Usage: python3 bin/ratify_terminal_promotion.py [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.aider_live_execution_gate import evaluate_aider_live_gate
from framework.aider_live_proof import run_aider_live_proof
from framework.aider_promotion_ratifier import ratify_aider_promotion
from framework.codex_availability_gate import evaluate_codex_availability
from framework.codex_promotion_ratifier import ratify_codex_promotion
from framework.cmdb_promotion_evidence import evaluate_cmdb_promotion_evidence
from framework.cmdb_promotion_ratifier import ratify_cmdb_promotion
from framework.domain_branch_first_wave_ratifier import ratify_first_wave_promotion
from framework.domain_branch_second_wave_ratifier import ratify_second_wave_promotion
from framework.terminal_promotion_ratifier import ratify_terminal_promotion


def main() -> int:
    parser = argparse.ArgumentParser(description="Ratify terminal promotion for LAPC1.")
    parser.add_argument("--artifact-dir", default="artifacts/terminal_promotion")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    gate = evaluate_aider_live_gate(dry_run=True)
    proof = run_aider_live_proof(gate, num_runs=3, dry_run=True)
    avail = evaluate_codex_availability(dry_run=True)
    evidence = evaluate_cmdb_promotion_evidence(dry_run=True)

    aider_a = ratify_aider_promotion(gate, proof, dry_run=True)
    codex_a = ratify_codex_promotion(avail, dry_run=True)
    cmdb_a = ratify_cmdb_promotion(evidence, dry_run=True)
    first_a = ratify_first_wave_promotion(dry_run=True)
    second_a = ratify_second_wave_promotion(dry_run=True)

    artifact = ratify_terminal_promotion(
        aider_artifact=aider_a,
        codex_artifact=codex_a,
        cmdb_artifact=cmdb_a,
        first_wave_artifact=first_a,
        second_wave_artifact=second_a,
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nCampaign: {artifact.campaign_id}")
    print(f"Decision: {artifact.decision}")
    print(f"Resolved: {artifact.resolved_count}/{artifact.total_count}")
    if artifact.unresolved_items:
        print(f"Unresolved items: {artifact.unresolved_items}")
    print()
    print(f"{'Item':<28} {'Expected':<40} {'Actual':<40} {'OK'}")
    print("-" * 115)
    for r in artifact.records:
        ok = "Y" if r.resolved else "N"
        print(f"  {r.item_key:<26} {r.expected_resolution:<40} {r.actual_resolution:<40} {ok}")

    if not args.dry_run and artifact.artifact_path:
        print(f"\nArtifact: {artifact.artifact_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
