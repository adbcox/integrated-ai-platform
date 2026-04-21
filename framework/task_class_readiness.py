"""Per-task-class readiness verdicts derived from TaskClassMetrics evidence."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.autonomy_evidence import TaskClassMetrics

# -- import-time assertions --
assert "task_class" in TaskClassMetrics.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassMetrics.task_class"
assert "total_attempts" in TaskClassMetrics.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassMetrics.total_attempts"
assert "successes" in TaskClassMetrics.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassMetrics.successes"
assert "failure_rate" in TaskClassMetrics.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassMetrics.failure_rate"
assert "routed_profile" in TaskClassMetrics.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassMetrics.routed_profile"

_VALID_VERDICTS = frozenset({"ready", "marginal", "not_ready"})
_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "task_class_readiness"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class TaskClassVerdict:
    task_class: str
    verdict: str
    failure_rate: float
    total_attempts: int
    rationale: str


@dataclass(frozen=True)
class TaskClassReadinessReport:
    verdicts: tuple
    overall_verdict: str
    ready_count: int
    marginal_count: int
    not_ready_count: int
    evaluated_at: str


def derive_task_class_readiness(
    metrics: List[TaskClassMetrics],
    *,
    ready_threshold: float = 0.15,
    marginal_threshold: float = 0.35,
    min_attempts: int = 3,
) -> TaskClassReadinessReport:
    verdicts = []
    for m in metrics:
        if m.total_attempts < min_attempts:
            v = TaskClassVerdict(
                task_class=m.task_class,
                verdict="marginal",
                failure_rate=m.failure_rate,
                total_attempts=m.total_attempts,
                rationale="insufficient evidence",
            )
        elif m.failure_rate <= ready_threshold:
            v = TaskClassVerdict(
                task_class=m.task_class,
                verdict="ready",
                failure_rate=m.failure_rate,
                total_attempts=m.total_attempts,
                rationale=f"failure_rate {m.failure_rate:.3f} <= ready threshold {ready_threshold}",
            )
        elif m.failure_rate <= marginal_threshold:
            v = TaskClassVerdict(
                task_class=m.task_class,
                verdict="marginal",
                failure_rate=m.failure_rate,
                total_attempts=m.total_attempts,
                rationale=f"failure_rate {m.failure_rate:.3f} <= marginal threshold {marginal_threshold}",
            )
        else:
            v = TaskClassVerdict(
                task_class=m.task_class,
                verdict="not_ready",
                failure_rate=m.failure_rate,
                total_attempts=m.total_attempts,
                rationale=f"failure_rate {m.failure_rate:.3f} > marginal threshold {marginal_threshold}",
            )
        verdicts.append(v)

    ready_count = sum(1 for v in verdicts if v.verdict == "ready")
    marginal_count = sum(1 for v in verdicts if v.verdict == "marginal")
    not_ready_count = sum(1 for v in verdicts if v.verdict == "not_ready")

    if not_ready_count > 0:
        overall = "not_ready"
    elif marginal_count > 0:
        overall = "marginal"
    elif ready_count > 0:
        overall = "ready"
    else:
        overall = "marginal"  # empty list → no evidence

    return TaskClassReadinessReport(
        verdicts=tuple(verdicts),
        overall_verdict=overall,
        ready_count=ready_count,
        marginal_count=marginal_count,
        not_ready_count=not_ready_count,
        evaluated_at=_iso_now(),
    )


def emit_readiness_report(
    report: TaskClassReadinessReport,
    *,
    artifact_dir: Path = _DEFAULT_ARTIFACT_DIR,
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "task_class_readiness.json"
    out_path.write_text(
        json.dumps(
            {
                "overall_verdict": report.overall_verdict,
                "ready_count": report.ready_count,
                "marginal_count": report.marginal_count,
                "not_ready_count": report.not_ready_count,
                "evaluated_at": report.evaluated_at,
                "verdicts": [
                    {
                        "task_class": v.task_class,
                        "verdict": v.verdict,
                        "failure_rate": v.failure_rate,
                        "total_attempts": v.total_attempts,
                        "rationale": v.rationale,
                    }
                    for v in report.verdicts
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = [
    "TaskClassVerdict",
    "TaskClassReadinessReport",
    "derive_task_class_readiness",
    "emit_readiness_report",
]
