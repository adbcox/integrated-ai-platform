"""LACE1-P6-EXECUTION-TRACE-ENRICHMENT-SEAM-1: typed enriched trace from ExecutionTraceResult."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.execution_trace_result_schema import ExecutionTraceResult

assert "result_id" in ExecutionTraceResult.__dataclass_fields__, "INTERFACE MISMATCH: ExecutionTraceResult.result_id"
assert "result_state" in ExecutionTraceResult.__dataclass_fields__, "INTERFACE MISMATCH: ExecutionTraceResult.result_state"
assert "completed_trace_items" in ExecutionTraceResult.__dataclass_fields__, "INTERFACE MISMATCH: ExecutionTraceResult.completed_trace_items"

_OUTCOME_CLASSES = {"first_pass_success", "retry_success", "failure", "partial"}
_FAILED_STATES = {"failed", "error", "failure"}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass(frozen=True)
class EnrichedTrace:
    trace_id: str
    source_result_id: str
    outcome_class: str      # "first_pass_success"|"retry_success"|"failure"|"partial"
    retry_count: int
    file_change_count: int
    outcome_state: str
    enriched_at: str


class ExecutionTraceEnricher:
    """Classifies ExecutionTraceResult into a typed EnrichedTrace."""

    def enrich(self, result: ExecutionTraceResult, *, retry_count: int = 0) -> EnrichedTrace:
        state = (result.result_state or "").lower()
        file_change_count = len(result.completed_trace_items) if result.completed_trace_items else 0

        if state in _FAILED_STATES:
            outcome_class = "failure"
        elif state == "complete":
            if retry_count == 0:
                outcome_class = "first_pass_success"
            else:
                outcome_class = "retry_success"
        else:
            outcome_class = "partial"

        assert outcome_class in _OUTCOME_CLASSES

        trace_id = f"ETRACE-{result.result_id}-{_ts()}"
        return EnrichedTrace(
            trace_id=trace_id,
            source_result_id=result.result_id,
            outcome_class=outcome_class,
            retry_count=retry_count,
            file_change_count=file_change_count,
            outcome_state=result.result_state,
            enriched_at=_iso_now(),
        )

    def emit_enriched(self, trace: EnrichedTrace, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / f"{trace.trace_id}.json"
        out_path.write_text(
            json.dumps(
                {
                    "trace_id": trace.trace_id,
                    "source_result_id": trace.source_result_id,
                    "outcome_class": trace.outcome_class,
                    "retry_count": trace.retry_count,
                    "file_change_count": trace.file_change_count,
                    "outcome_state": trace.outcome_state,
                    "enriched_at": trace.enriched_at,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return str(out_path)


__all__ = ["EnrichedTrace", "ExecutionTraceEnricher"]
