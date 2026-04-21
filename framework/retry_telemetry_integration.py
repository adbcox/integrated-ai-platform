"""LoopRetryTelemetryIntegration — adopts existing retry_telemetry surface for loop attempt recording.

Inspection gate output:
  retry_telemetry module exports: RetryTelemetryRecord (frozen dataclass), record_retry_telemetry(summary, *, artifact_dir)
  RetryTelemetryRecord fields: session_id, job_id, total_steps, failed_steps, retry_eligible_failures, outcome, recorded_at
  MVPLoopResult fields: task_kind, success, inspect_ok, patch_applied, test_passed, reverted, artifact_path,
                        validation_artifact_path, error
  Note: No RetryTelemetryStore class exists; integration uses append-to-JSONL store.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

from framework.mvp_coding_loop import MVPLoopResult
from framework.retry_telemetry import RetryTelemetryRecord, record_retry_telemetry

assert hasattr(RetryTelemetryRecord, "__dataclass_fields__"), "INTERFACE MISMATCH: RetryTelemetryRecord not dataclass"
assert callable(record_retry_telemetry), "INTERFACE MISMATCH: record_retry_telemetry not callable"
assert hasattr(MVPLoopResult, "__dataclass_fields__"), "INTERFACE MISMATCH: MVPLoopResult not dataclass"

_DEFAULT_STORE_DIR = Path("artifacts") / "retry_telemetry_integration"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _derive_error_type(loop_result: MVPLoopResult) -> str:
    if loop_result.success:
        return "none"
    err = loop_result.error or ""
    if "syntax" in err.lower():
        return "syntax_error"
    if "patch" in err.lower():
        return "patch_error"
    if "test" in err.lower():
        return "test_failure"
    return "other"


@dataclass
class LoopRetryIntegrationRecord:
    session_id: str
    task_kind: str
    attempt_number: int
    success: bool
    error_type: str
    recorded_at: str

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "task_kind": self.task_kind,
            "attempt_number": self.attempt_number,
            "success": self.success,
            "error_type": self.error_type,
            "recorded_at": self.recorded_at,
        }


class LoopRetryStore:
    """Simple append-only JSONL store for per-loop-attempt telemetry records."""

    def __init__(self, store_dir: Optional[Path] = None) -> None:
        self._store_dir = Path(store_dir) if store_dir is not None else _DEFAULT_STORE_DIR

    def append(self, record: LoopRetryIntegrationRecord) -> None:
        self._store_dir.mkdir(parents=True, exist_ok=True)
        store_file = self._store_dir / "loop_attempts.jsonl"
        with open(store_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def query_all(self) -> list:
        store_file = self._store_dir / "loop_attempts.jsonl"
        if not store_file.exists():
            return []
        records = []
        for line in store_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return records

    def query_by_session(self, session_id: str) -> list:
        return [r for r in self.query_all() if r.get("session_id") == session_id]


def record_loop_attempt(
    loop_result: MVPLoopResult,
    telemetry_store: LoopRetryStore,
    *,
    attempt_number: int,
    session_id: Optional[str] = None,
) -> LoopRetryIntegrationRecord:
    sid = session_id or "default"
    error_type = _derive_error_type(loop_result)
    record = LoopRetryIntegrationRecord(
        session_id=sid,
        task_kind=loop_result.task_kind or "unknown",
        attempt_number=attempt_number,
        success=bool(loop_result.success),
        error_type=error_type,
        recorded_at=_iso_now(),
    )
    telemetry_store.append(record)
    return record


def record_loop_attempt_batch(
    loop_results: Sequence[MVPLoopResult],
    telemetry_store: LoopRetryStore,
    *,
    session_id: Optional[str] = None,
) -> list:
    records = []
    for i, lr in enumerate(loop_results, start=1):
        record = record_loop_attempt(lr, telemetry_store, attempt_number=i, session_id=session_id)
        records.append(record)
    return records


__all__ = [
    "LoopRetryIntegrationRecord",
    "LoopRetryStore",
    "record_loop_attempt",
    "record_loop_attempt_batch",
]
