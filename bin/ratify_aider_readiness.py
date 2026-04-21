#!/usr/bin/env python3
"""Aider readiness ratifier.

Usage: python3 bin/ratify_aider_readiness.py [--evaluation-path PATH] [--artifact-dir PATH] [--dry-run]

Loads a ReadinessEvaluation (from file or live), ratifies the decision, and prints result.
Exits 0 always.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.readiness_evaluator import ReadinessEvaluation, evaluate_readiness
from framework.readiness_ratifier import ratify


def _load_evaluation(evaluation_path: Optional[str]) -> ReadinessEvaluation:
    if evaluation_path and Path(evaluation_path).exists():
        data = json.loads(Path(evaluation_path).read_text(encoding="utf-8"))
        from framework.readiness_evaluator import ReadinessCriterion
        criteria = [ReadinessCriterion(**c) for c in data.get("criteria", [])]
        return ReadinessEvaluation(
            readiness_verdict=data["readiness_verdict"],
            total_attempts=data["total_attempts"],
            overall_failure_rate=data["overall_failure_rate"],
            escalation_rate=data["escalation_rate"],
            criteria=criteria,
            all_criteria_passed=data["all_criteria_passed"],
            defer_reasons=data.get("defer_reasons", []),
            evidence_snapshot=data.get("evidence_snapshot", {}),
            evaluated_at=data.get("evaluated_at", ""),
        )
    return evaluate_readiness(dry_run=True)


from typing import Optional


def main() -> int:
    parser = argparse.ArgumentParser(description="Ratify Aider adapter readiness.")
    parser.add_argument("--evaluation-path", default=None)
    parser.add_argument("--artifact-dir", default="artifacts/readiness")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    evaluation = _load_evaluation(args.evaluation_path)
    artifact = ratify(
        evaluation,
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nDecision: {artifact.decision}")
    print(f"Attempts: {artifact.total_attempts}")
    print(f"All criteria passed: {artifact.all_criteria_passed}")
    print()
    print(f"Next steps: {artifact.next_steps}")
    print()

    if artifact.defer_reasons:
        print("Defer reasons:")
        for r in artifact.defer_reasons:
            print(f"  - {r}")
        print()

    if not args.dry_run and artifact.artifact_path:
        print(f"Artifact: {artifact.artifact_path}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
