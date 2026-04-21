#!/usr/bin/env python3
"""Standalone LAUC1 local-autonomy evidence runner.

Usage: python3 bin/lauc1_evidence_run.py [--artifact-dir PATH] [--dry-run]

Collects local autonomy evidence from the memory store, prints a per-task-class
table, and emits the evidence artifact. Exits 0 always (evidence collection is
not a pass/fail gate — it is a measurement).

Aider readiness is surfaced in the output for control-window review.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.autonomy_evidence import collect_autonomy_evidence
from framework.local_memory_store import LocalMemoryStore


def _fmt_rate(rate: float) -> str:
    return f"{rate:.1%}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect LAUC1 local-autonomy evidence.")
    parser.add_argument("--artifact-dir", default="artifacts/autonomy_evidence")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = collect_autonomy_evidence(
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    # Print per-task-class table
    print(f"\n{'TASK CLASS':<28} {'ATTEMPTS':>9} {'PASS':>6} {'FAIL':>6} {'FAIL%':>8} {'PROFILE':<12} {'ESC'}")
    print("-" * 82)
    for m in result.task_class_metrics:
        esc_flag = "YES" if m["escalated"] else "-"
        print(
            f"{m['task_class']:<28} "
            f"{m['total_attempts']:>9} "
            f"{m['successes']:>6} "
            f"{m['failures']:>6} "
            f"{_fmt_rate(m['failure_rate']):>8} "
            f"{m['routed_profile']:<12} "
            f"{esc_flag}"
        )

    print("-" * 82)
    print(
        f"{'OVERALL':<28} "
        f"{result.overall_success_count + result.overall_failure_count:>9} "
        f"{result.overall_success_count:>6} "
        f"{result.overall_failure_count:>6} "
        f"{_fmt_rate(result.overall_failure_rate):>8}"
    )
    print()
    print(f"Escalation rate : {_fmt_rate(result.escalation_rate)}")
    print()
    print(f"Aider readiness : {result.aider_readiness_decision}")
    print(f"Reason          : {result.aider_readiness_reason}")
    print()

    if not args.dry_run and result.artifact_path:
        print(f"Evidence artifact : {result.artifact_path}")
    if not args.dry_run and result.validation_artifact_path:
        print(f"Validation record : {result.validation_artifact_path}")

    print()
    print(f"Campaign: LOCAL-AUTONOMY-UPLIFT-CAMPAIGN-1 evidence collected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
