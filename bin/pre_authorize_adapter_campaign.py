#!/usr/bin/env python3
"""Adapter campaign pre-authorizer.

Usage: python3 bin/pre_authorize_adapter_campaign.py [--ratification-path PATH] [--artifact-dir PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.adapter_campaign_pre_authorizer import pre_authorize_adapter_campaign


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-authorize adapter campaign.")
    parser.add_argument("--ratification-path", default=None)
    parser.add_argument("--artifact-dir", default="artifacts/pre_authorization")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ratification = None
    if args.ratification_path and Path(args.ratification_path).exists():
        from framework.readiness_ratifier import RatificationArtifact, RatificationDecision
        from framework.readiness_evaluator import ReadinessCriterion
        data = json.loads(Path(args.ratification_path).read_text(encoding="utf-8"))
        from dataclasses import dataclass
        ratification = RatificationArtifact(
            campaign_id=data.get("campaign_id", ""),
            decision=data.get("decision", ""),
            ratified_at=data.get("ratified_at", ""),
            total_attempts=data.get("total_attempts", 0),
            all_criteria_passed=data.get("all_criteria_passed", False),
            criteria_summary=data.get("criteria_summary", []),
            defer_reasons=data.get("defer_reasons", []),
            next_steps=data.get("next_steps", ""),
        )

    artifact = pre_authorize_adapter_campaign(
        ratification_artifact=ratification,
        artifact_dir=Path(args.artifact_dir),
        dry_run=args.dry_run,
    )

    print(f"\nDecision: {artifact.decision}")
    print(f"All gates passed: {artifact.all_gates_passed}")
    print()
    print("Gate table:")
    for g in artifact.gates:
        status = "PASS" if g.passed else "FAIL"
        print(f"  [{status}] {g.gate_name}: observed={g.observed_value} required={g.required_value}")
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
