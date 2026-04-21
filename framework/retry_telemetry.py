"""Typed retry telemetry derived from BoundedExecutionSummary step results."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.runtime_execution_adapter import BoundedExecutionSummary, ExecutionStepResult

# -- import-time assertions --
assert "steps" in BoundedExecutionSummary.__dataclass_fields__, \
    "INTERFACE MISMATCH: BoundedExecutionSummary.steps"
assert "outcome" in BoundedExecutionSummary.__dataclass_fields__, \
    "INTERFACE MISMATCH: BoundedExecutionSummary.outcome"
assert "session_id" in BoundedExecutionSummary.__dataclass_fields__, \
    "INTERFACE MISMATCH: BoundedExecutionSummary.session_id"
assert "job_id" in BoundedExecutionSummary.__dataclass_fields__, \
    "INTERFACE MISMATCH: BoundedExecutionSummary.job_id"
assert "success" in ExecutionStepResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: ExecutionStepResult.success"
assert "error" in ExecutionStepResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: ExecutionStepResult.error"

_DEFAULT_ARTIFACT_DIR = Path("artifacts") / "retry_telemetry"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class RetryTelemetryRecord:
    session_id: str
    job_id: str
    total_steps: int
    failed_steps: int
    retry_eligible_failures: int
    outcome: str
    recorded_at: str


def record_retry_telemetry(
    summary: BoundedExecutionSummary,
    *,
    artifact_dir: Optional[Path] = None,
) -> RetryTelemetryRecord:
    art_dir = Path(artifact_dir) if artifact_dir is not None else _DEFAULT_ARTIFACT_DIR
    art_dir.mkdir(parents=True, exist_ok=True)

    failed_steps = 0
    retry_eligible = 0
    for step in summary.steps:
        if not step.success:
            failed_steps += 1
            if step.error is not None:
                retry_eligible += 1

    record = RetryTelemetryRecord(
        session_id=summary.session_id,
        job_id=summary.job_id,
        total_steps=summary.total_steps,
        failed_steps=failed_steps,
        retry_eligible_failures=retry_eligible,
        outcome=summary.outcome,
        recorded_at=_iso_now(),
    )

    out_path = art_dir / f"retry_telemetry_{summary.job_id}.json"
    out_path.write_text(
        json.dumps(
            {
                "session_id": record.session_id,
                "job_id": record.job_id,
                "total_steps": record.total_steps,
                "failed_steps": record.failed_steps,
                "retry_eligible_failures": record.retry_eligible_failures,
                "outcome": record.outcome,
                "recorded_at": record.recorded_at,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return record


__all__ = ["RetryTelemetryRecord", "record_retry_telemetry"]
