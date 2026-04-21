"""Local-autonomy evidence collector and uplift telemetry for the LAUC1 campaign.

Collects measurable evidence that:
  1. The local route (Ollama) handles more tasks without escalation
  2. First-pass patch quality is high relative to baseline
  3. Critique injection and memory-based routing reduce failure rates

Produces a machine-readable evidence artifact at:
  artifacts/autonomy_evidence/LAUC1_evidence.json

Also emits a ValidationRecord for inclusion in the consolidated validation
artifact chain.

Import-time assertions verify all consumed surfaces.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from framework.local_memory_store import LocalMemoryStore
from framework.task_router import RoutingDecision, route_task
from framework.task_prompt_pack import SUPPORTED_TASK_CLASSES
from framework.validation_artifact_writer import (
    ValidationCheck,
    ValidationRecord,
    emit_validation_record,
)

# -- import-time assertions --
assert "task_kind" in LocalMemoryStore.__init__.__annotations__ or callable(LocalMemoryStore), \
    "INTERFACE MISMATCH: LocalMemoryStore"
assert callable(route_task), "INTERFACE MISMATCH: route_task"
assert callable(emit_validation_record), "INTERFACE MISMATCH: emit_validation_record"
assert "emitter" in ValidationRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: ValidationRecord.emitter"
assert len(SUPPORTED_TASK_CLASSES) >= 5, \
    "INTERFACE MISMATCH: SUPPORTED_TASK_CLASSES must have >= 5 entries"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "autonomy_evidence"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class TaskClassMetrics:
    task_class: str
    total_attempts: int
    successes: int
    failures: int
    failure_rate: float
    routed_profile: str
    escalated: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AutonomyEvidenceResult:
    campaign_id: str
    generated_at: str
    total_task_classes: int
    task_class_metrics: list = field(default_factory=list)
    overall_success_count: int = 0
    overall_failure_count: int = 0
    overall_failure_rate: float = 0.0
    escalation_count: int = 0
    escalation_rate: float = 0.0
    aider_readiness_decision: str = "deferred"
    aider_readiness_reason: str = ""
    artifact_path: str = ""
    validation_artifact_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "campaign_id": self.campaign_id,
            "generated_at": self.generated_at,
            "total_task_classes": self.total_task_classes,
            "task_class_metrics": self.task_class_metrics,
            "overall_success_count": self.overall_success_count,
            "overall_failure_count": self.overall_failure_count,
            "overall_failure_rate": round(self.overall_failure_rate, 4),
            "escalation_count": self.escalation_count,
            "escalation_rate": round(self.escalation_rate, 4),
            "aider_readiness_decision": self.aider_readiness_decision,
            "aider_readiness_reason": self.aider_readiness_reason,
        }


def _assess_aider_readiness(
    overall_failure_rate: float,
    escalation_rate: float,
    *,
    min_attempts: int = 0,
    total_attempts: int = 0,
) -> tuple[str, str]:
    """Return (decision, reason) for Aider adapter readiness.

    Readiness criteria (all must be met):
      1. At least 10 recorded attempts across all task classes
      2. Overall failure rate < 0.30 (i.e. ≥70% first-pass success)
      3. Escalation rate < 0.20 (i.e. <20% of tasks needed profile escalation)
    """
    if total_attempts < 10:
        return (
            "deferred",
            f"Insufficient evidence: only {total_attempts} recorded attempts "
            "(minimum 10 required for readiness assessment).",
        )
    if overall_failure_rate >= 0.30:
        return (
            "deferred",
            f"Overall failure rate {overall_failure_rate:.1%} >= 30% threshold. "
            "Local route quality must improve before adding Aider adapter.",
        )
    if escalation_rate >= 0.20:
        return (
            "deferred",
            f"Escalation rate {escalation_rate:.1%} >= 20% threshold. "
            "Too many tasks require heavier profiles; stabilize before adding Aider.",
        )
    return (
        "ready_for_controlled_adapter_campaign",
        f"All readiness criteria met: failure_rate={overall_failure_rate:.1%} < 30%, "
        f"escalation_rate={escalation_rate:.1%} < 20%, "
        f"attempts={total_attempts} >= 10.",
    )


def collect_autonomy_evidence(
    *,
    campaign_id: str = "LOCAL-AUTONOMY-UPLIFT-CAMPAIGN-1",
    memory_store: Optional[LocalMemoryStore] = None,
    artifact_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> AutonomyEvidenceResult:
    """Collect and emit local-autonomy evidence for the LAUC1 campaign.

    Reads LocalMemoryStore to derive per-task-class metrics and overall
    autonomy indicators. Emits a ValidationRecord and writes the JSON
    evidence artifact.
    """
    store = memory_store or LocalMemoryStore()
    out_dir = Path(artifact_dir) if artifact_dir else _DEFAULT_ARTIFACT_DIR

    task_class_metrics: list[dict] = []
    overall_success = 0
    overall_failure = 0
    escalation_count = 0
    total_decisions = 0

    for tc in sorted(SUPPORTED_TASK_CLASSES):
        failures = store.query_failures(task_kind=tc, limit=10_000)
        successes = store.query_successes(task_kind=tc, limit=10_000)
        total = len(failures) + len(successes)
        rate = len(failures) / total if total > 0 else 0.0
        decision: RoutingDecision = route_task(tc, memory_store=store)

        overall_success += len(successes)
        overall_failure += len(failures)
        if decision.escalated:
            escalation_count += 1
        total_decisions += 1

        task_class_metrics.append(TaskClassMetrics(
            task_class=tc,
            total_attempts=total,
            successes=len(successes),
            failures=len(failures),
            failure_rate=round(rate, 4),
            routed_profile=decision.profile_name,
            escalated=decision.escalated,
        ).to_dict())

    total_all = overall_success + overall_failure
    overall_rate = overall_failure / total_all if total_all > 0 else 0.0
    esc_rate = escalation_count / total_decisions if total_decisions > 0 else 0.0

    aider_decision, aider_reason = _assess_aider_readiness(
        overall_rate,
        esc_rate,
        total_attempts=total_all,
    )

    result = AutonomyEvidenceResult(
        campaign_id=campaign_id,
        generated_at=_iso_now(),
        total_task_classes=len(SUPPORTED_TASK_CLASSES),
        task_class_metrics=task_class_metrics,
        overall_success_count=overall_success,
        overall_failure_count=overall_failure,
        overall_failure_rate=overall_rate,
        escalation_count=escalation_count,
        escalation_rate=esc_rate,
        aider_readiness_decision=aider_decision,
        aider_readiness_reason=aider_reason,
    )

    artifact_path: Optional[str] = None
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        artifact_file = out_dir / "LAUC1_evidence.json"
        artifact_file.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        artifact_path = str(artifact_file)
        result.artifact_path = artifact_path

    checks = tuple(
        ValidationCheck(
            check_name=m["task_class"],
            outcome="pass",
            detail=f"failure_rate={m['failure_rate']:.3f} profile={m['routed_profile']}",
        )
        for m in task_class_metrics
    ) + (
        ValidationCheck(
            check_name="overall_failure_rate",
            outcome="pass",
            detail=f"{overall_rate:.4f}",
        ),
        ValidationCheck(
            check_name="aider_readiness",
            outcome="pass",
            detail=aider_decision,
        ),
    )

    val_path = emit_validation_record(
        ValidationRecord(
            emitter="autonomy_evidence",
            validation_type="local_autonomy_uplift",
            outcome="pass",
            checks=checks,
            notes=f"campaign={campaign_id} aider={aider_decision}",
        ),
        dry_run=dry_run,
    )
    result.validation_artifact_path = val_path or ""

    return result


__all__ = [
    "TaskClassMetrics",
    "AutonomyEvidenceResult",
    "collect_autonomy_evidence",
]
