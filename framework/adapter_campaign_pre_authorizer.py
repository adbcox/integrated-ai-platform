"""AdapterCampaignPreAuthorizer — structured gate for a future controlled adapter campaign.

Inspection gate output:
  RatificationArtifact fields: campaign_id, decision, ratified_at, total_attempts,
    all_criteria_passed, criteria_summary, defer_reasons, next_steps, artifact_path
  ThresholdTuningResult fields: recommendations, total_classes, classes_with_recommendation,
    generated_at, artifact_path
  FirstPassReport fields: stats, overall_first_pass_successes, overall_retry_successes,
    overall_attempts, overall_first_pass_rate, generated_at, artifact_path

NO adapter implementation in this module.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.first_pass_metric import FirstPassReport
from framework.readiness_ratifier import RatificationArtifact
from framework.threshold_tuner import ThresholdTuningResult

assert hasattr(RatificationArtifact, "__dataclass_fields__"), "INTERFACE MISMATCH: RatificationArtifact not dataclass"
assert hasattr(ThresholdTuningResult, "__dataclass_fields__"), "INTERFACE MISMATCH: ThresholdTuningResult not dataclass"
assert hasattr(FirstPassReport, "__dataclass_fields__"), "INTERFACE MISMATCH: FirstPassReport not dataclass"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "pre_authorization"

PRE_AUTH_DECISION_AUTHORIZED = "pre_authorized"
PRE_AUTH_DECISION_DEFERRED = "deferred_pending_gates"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class PreAuthGate:
    gate_name: str
    passed: bool
    observed_value: str
    required_value: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "gate_name": self.gate_name,
            "passed": self.passed,
            "observed_value": self.observed_value,
            "required_value": self.required_value,
            "reason": self.reason,
        }


@dataclass
class PreAuthorizationArtifact:
    campaign_id: str
    decision: str
    gates: list
    all_gates_passed: bool
    defer_reasons: list
    next_steps: str
    generated_at: str
    artifact_path: str = ""

    def to_dict(self) -> dict:
        return {
            "schema_version": 1,
            "campaign_id": self.campaign_id,
            "decision": self.decision,
            "all_gates_passed": self.all_gates_passed,
            "defer_reasons": self.defer_reasons,
            "next_steps": self.next_steps,
            "generated_at": self.generated_at,
            "gates": [g.to_dict() for g in self.gates],
        }


def pre_authorize_adapter_campaign(
    *,
    ratification_artifact: Optional[RatificationArtifact] = None,
    tuning_result: Optional[ThresholdTuningResult] = None,
    first_pass_report: Optional[FirstPassReport] = None,
    campaign_id: str = "LOCAL-AUTONOMY-RUNTIME-ADOPTION-CAMPAIGN-1",
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> PreAuthorizationArtifact:
    gates = []

    # Gate 1: Ratification decision
    if ratification_artifact is not None:
        passed = ratification_artifact.all_criteria_passed
        gates.append(PreAuthGate(
            gate_name="readiness_ratification",
            passed=passed,
            observed_value=ratification_artifact.decision,
            required_value="ready_for_controlled_adapter_campaign",
            reason="Readiness ratification must be READY" if not passed else "Ratification passed",
        ))
    else:
        gates.append(PreAuthGate(
            gate_name="readiness_ratification",
            passed=False,
            observed_value="not_provided",
            required_value="ready_for_controlled_adapter_campaign",
            reason="No ratification artifact provided",
        ))

    # Gate 2: Threshold tuning evidence
    if tuning_result is not None:
        passed = tuning_result.total_classes > 0
        gates.append(PreAuthGate(
            gate_name="threshold_tuning",
            passed=passed,
            observed_value=f"classes={tuning_result.total_classes}",
            required_value="total_classes>0",
            reason="Threshold tuning must have at least one class" if not passed else "Threshold tuning present",
        ))
    else:
        gates.append(PreAuthGate(
            gate_name="threshold_tuning",
            passed=False,
            observed_value="not_provided",
            required_value="total_classes>0",
            reason="No threshold tuning result provided",
        ))

    # Gate 3: First-pass evidence
    if first_pass_report is not None:
        passed = first_pass_report.overall_attempts >= 0
        gates.append(PreAuthGate(
            gate_name="first_pass_evidence",
            passed=True,
            observed_value=f"attempts={first_pass_report.overall_attempts}",
            required_value="present",
            reason="First pass evidence provided",
        ))
    else:
        gates.append(PreAuthGate(
            gate_name="first_pass_evidence",
            passed=False,
            observed_value="not_provided",
            required_value="present",
            reason="No first pass report provided",
        ))

    all_passed = all(g.passed for g in gates)
    defer_reasons = [g.reason for g in gates if not g.passed]

    if all_passed:
        decision = PRE_AUTH_DECISION_AUTHORIZED
        next_steps = (
            "All pre-authorization gates passed. A future controlled adapter campaign may reference "
            "this artifact as authorization to begin bounded adapter integration. "
            "No adapter code is included in this pre-authorization."
        )
    else:
        decision = PRE_AUTH_DECISION_DEFERRED
        reasons_text = "; ".join(defer_reasons) or "one or more gates failed"
        next_steps = (
            f"Pre-authorization deferred: {reasons_text}. "
            "Resolve all gate failures before proceeding. Do not implement adapter code."
        )

    artifact = PreAuthorizationArtifact(
        campaign_id=campaign_id,
        decision=decision,
        gates=gates,
        all_gates_passed=all_passed,
        defer_reasons=defer_reasons,
        next_steps=next_steps,
        generated_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "pre_authorization.json"
        out_path.write_text(
            json.dumps(artifact.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifact.artifact_path = str(out_path)

    return artifact


__all__ = [
    "PreAuthGate",
    "PreAuthorizationArtifact",
    "PRE_AUTH_DECISION_AUTHORIZED",
    "PRE_AUTH_DECISION_DEFERRED",
    "pre_authorize_adapter_campaign",
]
