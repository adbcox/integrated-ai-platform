"""Structured Aider readiness evaluator.

Produces a machine-readable ReadinessEvaluation artifact from live evidence.
Evaluates 3 criteria: attempts >= 10, failure_rate < 0.30, escalation_rate < 0.20.

Inspection gate output (packet 9):
  AutonomyEvidenceResult fields: campaign_id, generated_at, total_task_classes,
    task_class_metrics, overall_success_count, overall_failure_count,
    overall_failure_rate, escalation_count, escalation_rate, aider_readiness_decision,
    aider_readiness_reason, artifact_path, validation_artifact_path
  collect_extended_metrics: accessible and callable
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from framework.autonomy_evidence import AutonomyEvidenceResult, collect_autonomy_evidence
from framework.autonomy_metrics_extended import ExtendedAutonomyMetrics, collect_extended_metrics
from framework.local_memory_store import LocalMemoryStore

# -- import-time assertions --
assert callable(collect_autonomy_evidence), "INTERFACE MISMATCH: collect_autonomy_evidence"
assert callable(collect_extended_metrics), "INTERFACE MISMATCH: collect_extended_metrics"
assert "overall_failure_rate" in AutonomyEvidenceResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: AutonomyEvidenceResult.overall_failure_rate"
assert "escalation_rate" in AutonomyEvidenceResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: AutonomyEvidenceResult.escalation_rate"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "readiness"
_MIN_ATTEMPTS = 10
_MAX_FAILURE_RATE = 0.30
_MAX_ESCALATION_RATE = 0.20


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class ReadinessCriterion:
    name: str
    passed: bool
    observed_value: float
    threshold: float
    description: str


@dataclass
class ReadinessEvaluation:
    readiness_verdict: str
    total_attempts: int
    overall_failure_rate: float
    escalation_rate: float
    criteria: list[ReadinessCriterion] = field(default_factory=list)
    all_criteria_passed: bool = False
    defer_reasons: list[str] = field(default_factory=list)
    evidence_snapshot: dict[str, Any] = field(default_factory=dict)
    evaluated_at: str = field(default_factory=_iso_now)
    artifact_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "evaluated_at": self.evaluated_at,
            "readiness_verdict": self.readiness_verdict,
            "total_attempts": self.total_attempts,
            "overall_failure_rate": round(self.overall_failure_rate, 4),
            "escalation_rate": round(self.escalation_rate, 4),
            "all_criteria_passed": self.all_criteria_passed,
            "defer_reasons": self.defer_reasons,
            "criteria": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "observed_value": round(c.observed_value, 4),
                    "threshold": c.threshold,
                    "description": c.description,
                }
                for c in self.criteria
            ],
            "evidence_snapshot": self.evidence_snapshot,
        }

    def summary_lines(self) -> list[str]:
        lines = [
            f"Readiness verdict: {self.readiness_verdict}",
            f"Total attempts:    {self.total_attempts}",
            f"Failure rate:      {self.overall_failure_rate:.1%}",
            f"Escalation rate:   {self.escalation_rate:.1%}",
        ]
        for c in self.criteria:
            status = "PASS" if c.passed else "FAIL"
            lines.append(f"  [{status}] {c.name}: {c.observed_value:.4f} vs threshold {c.threshold}")
        if self.defer_reasons:
            lines.append("Defer reasons:")
            for r in self.defer_reasons:
                lines.append(f"  - {r}")
        return lines


def evaluate_readiness(
    *,
    campaign_id: str = "LOCAL-AUTONOMY-STABILITY-CLOSEOUT-CAMPAIGN-1",
    memory_store: Optional[LocalMemoryStore] = None,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> ReadinessEvaluation:
    """Evaluate Aider readiness against 3 criteria and produce structured artifact."""
    store = memory_store or LocalMemoryStore()

    evidence = collect_autonomy_evidence(
        campaign_id=campaign_id,
        memory_store=store,
        dry_run=True,
    )
    metrics = collect_extended_metrics(memory_store=store)

    total_attempts = evidence.overall_success_count + evidence.overall_failure_count
    failure_rate = evidence.overall_failure_rate
    escalation_rate = evidence.escalation_rate

    c_attempts = ReadinessCriterion(
        name="min_attempts",
        passed=total_attempts >= _MIN_ATTEMPTS,
        observed_value=float(total_attempts),
        threshold=float(_MIN_ATTEMPTS),
        description=f"At least {_MIN_ATTEMPTS} recorded attempts required",
    )
    c_failure = ReadinessCriterion(
        name="max_failure_rate",
        passed=failure_rate < _MAX_FAILURE_RATE,
        observed_value=failure_rate,
        threshold=_MAX_FAILURE_RATE,
        description=f"Overall failure rate must be < {_MAX_FAILURE_RATE:.0%}",
    )
    c_escalation = ReadinessCriterion(
        name="max_escalation_rate",
        passed=escalation_rate < _MAX_ESCALATION_RATE,
        observed_value=escalation_rate,
        threshold=_MAX_ESCALATION_RATE,
        description=f"Escalation rate must be < {_MAX_ESCALATION_RATE:.0%}",
    )

    criteria = [c_attempts, c_failure, c_escalation]
    all_passed = all(c.passed for c in criteria)
    defer_reasons = [c.description for c in criteria if not c.passed]

    verdict = "ready_for_controlled_adapter_campaign" if all_passed else "deferred_pending_evidence"

    evaluation = ReadinessEvaluation(
        readiness_verdict=verdict,
        total_attempts=total_attempts,
        overall_failure_rate=failure_rate,
        escalation_rate=escalation_rate,
        criteria=criteria,
        all_criteria_passed=all_passed,
        defer_reasons=defer_reasons,
        evidence_snapshot={
            "campaign_id": campaign_id,
            "aider_readiness_decision": evidence.aider_readiness_decision,
            "overall_first_pass_rate": round(metrics.overall_first_pass_rate, 4),
        },
        evaluated_at=_iso_now(),
    )

    if not dry_run:
        out_dir = Path(artifact_dir) if artifact_dir else _DEFAULT_ARTIFACT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        artifact_file = out_dir / "LASC1_readiness_evaluation.json"
        artifact_file.write_text(
            json.dumps(evaluation.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        evaluation.artifact_path = str(artifact_file)

    return evaluation


__all__ = [
    "ReadinessCriterion",
    "ReadinessEvaluation",
    "evaluate_readiness",
]
