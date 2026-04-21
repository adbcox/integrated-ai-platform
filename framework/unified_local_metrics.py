"""UnifiedLocalMetrics: combines extended autonomy metrics, retry telemetry, and task-class readiness."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.autonomy_metrics_extended import ExtendedAutonomyMetrics
from framework.retry_telemetry import RetryTelemetryRecord
from framework.task_class_readiness import TaskClassReadinessReport

# -- import-time assertions via field inspection --
_ext_fields = set(ExtendedAutonomyMetrics.__dataclass_fields__.keys())
assert "overall_first_pass_rate" in _ext_fields or any("first_pass" in f for f in _ext_fields), \
    "INTERFACE MISMATCH: ExtendedAutonomyMetrics missing first-pass-rate equivalent field"
assert "overall_failure_rate" in _ext_fields or any("failure_rate" in f for f in _ext_fields), \
    "INTERFACE MISMATCH: ExtendedAutonomyMetrics missing failure-rate equivalent field"
assert "retry_eligible_failures" in RetryTelemetryRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: RetryTelemetryRecord.retry_eligible_failures"
assert "overall_verdict" in TaskClassReadinessReport.__dataclass_fields__, \
    "INTERFACE MISMATCH: TaskClassReadinessReport.overall_verdict"

# Field mapping: use actual field names from ExtendedAutonomyMetrics
_FIRST_PASS_FIELD = (
    "overall_first_pass_rate"
    if "overall_first_pass_rate" in _ext_fields
    else next((f for f in _ext_fields if "first_pass" in f), None)
)
_FAILURE_RATE_FIELD = (
    "overall_failure_rate"
    if "overall_failure_rate" in _ext_fields
    else next((f for f in _ext_fields if "failure_rate" in f), None)
)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class UnifiedLocalMetrics:
    first_pass_rate: float
    failure_rate: float
    total_retry_burden: int
    readiness_verdict: str
    task_classes_total: int
    computed_at: str


def compute_unified_metrics(
    extended_metrics: ExtendedAutonomyMetrics,
    *,
    retry_records: Optional[List[RetryTelemetryRecord]] = None,
    readiness_report: Optional[TaskClassReadinessReport] = None,
) -> UnifiedLocalMetrics:
    retry_records = retry_records or []

    # Use inspection-mapped field names
    first_pass_rate: float = getattr(extended_metrics, _FIRST_PASS_FIELD, 0.0) or 0.0
    failure_rate: float = getattr(extended_metrics, _FAILURE_RATE_FIELD, 0.0) or 0.0
    total_task_classes: int = getattr(extended_metrics, "total_task_classes", 0) or 0

    total_retry_burden = sum(r.retry_eligible_failures for r in retry_records)
    readiness_verdict = (
        readiness_report.overall_verdict if readiness_report is not None else "unknown"
    )

    return UnifiedLocalMetrics(
        first_pass_rate=float(first_pass_rate),
        failure_rate=float(failure_rate),
        total_retry_burden=total_retry_burden,
        readiness_verdict=readiness_verdict,
        task_classes_total=total_task_classes,
        computed_at=_iso_now(),
    )


def emit_unified_metrics(
    metrics: UnifiedLocalMetrics,
    *,
    artifact_dir: Path = Path("artifacts") / "unified_metrics",
) -> str:
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifact_dir / "unified_local_metrics.json"
    out_path.write_text(
        json.dumps(
            {
                "first_pass_rate": metrics.first_pass_rate,
                "failure_rate": metrics.failure_rate,
                "total_retry_burden": metrics.total_retry_burden,
                "readiness_verdict": metrics.readiness_verdict,
                "task_classes_total": metrics.task_classes_total,
                "computed_at": metrics.computed_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return str(out_path)


__all__ = ["UnifiedLocalMetrics", "compute_unified_metrics", "emit_unified_metrics"]
