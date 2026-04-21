"""LACE2-P14-MINI-TRANCHE-IMPLEMENTATION-SEAM-1: MT2-TRACE-REPLAY-PIPELINE bounded proof."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from framework.execution_trace_enricher import ExecutionTraceEnricher, EnrichedTrace, _FAILED_STATES
from framework.execution_trace_result_schema import ExecutionTraceResult
from framework.replay_gate import ReplayGate, ReplaySpec

assert "outcome_class" in EnrichedTrace.__dataclass_fields__, "INTERFACE MISMATCH: EnrichedTrace.outcome_class"
assert "retry_count" in EnrichedTrace.__dataclass_fields__, "INTERFACE MISMATCH: EnrichedTrace.retry_count"
assert "file_change_count" in EnrichedTrace.__dataclass_fields__, "INTERFACE MISMATCH: EnrichedTrace.file_change_count"
assert "replayable" in ReplaySpec.__dataclass_fields__, "INTERFACE MISMATCH: ReplaySpec.replayable"

_FAILED_STATE_ONE = next(iter(_FAILED_STATES))

_PIPELINE_TRACE_DEFS = [
    ("PIPE-DECOMP",       "complete",        ["framework/scheduler.py"],             "",                 0),
    ("PIPE-RETRIEVAL",    "complete",        ["framework/worker_runtime.py"],        "",                 0),
    ("PIPE-REPAIR-RETRY", "complete",        ["framework/repair_policy_gate.py"],    "",                 1),
    ("PIPE-REPAIR-FAIL",  _FAILED_STATE_ONE, [],                                     "validation error", 0),
    ("PIPE-PARTIAL",      "partial",         ["framework/scheduler.py"],             "",                 0),
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass(frozen=True)
class PipelineStageResult:
    trace_id: str
    outcome_class: str
    retry_count: int
    replayable: bool
    replay_priority: str
    not_replayable_reason: Optional[str]


@dataclass
class TraceReplayPipelineRecord:
    pipeline_id: str
    selected_tranche: str
    total_traces: int
    enriched_count: int
    replayable_count: int
    not_replayable_count: int
    pipeline_stages: List[PipelineStageResult]
    proved_at: str
    artifact_path: Optional[str] = None


class TraceReplayPipelineRunner:
    """Connects enriched traces through the replay gate as a bounded pipeline proof."""

    def run(self) -> TraceReplayPipelineRecord:
        enricher = ExecutionTraceEnricher()
        gate = ReplayGate()

        stages: List[PipelineStageResult] = []

        for (result_id, state, items, notes, retry_count) in _PIPELINE_TRACE_DEFS:
            raw = ExecutionTraceResult(
                result_id=result_id,
                result_state=state,
                completed_trace_items=items,
                notes=notes,
            )
            enriched: EnrichedTrace = enricher.enrich(raw, retry_count=retry_count)
            spec: ReplaySpec = gate.evaluate(enriched)

            stages.append(PipelineStageResult(
                trace_id=result_id,
                outcome_class=enriched.outcome_class,
                retry_count=enriched.retry_count,
                replayable=spec.replayable,
                replay_priority=spec.replay_priority,
                not_replayable_reason=spec.not_replayable_reason,
            ))

        replayable_count = sum(1 for s in stages if s.replayable)

        return TraceReplayPipelineRecord(
            pipeline_id=f"LACE2-PIPE-{_ts()}",
            selected_tranche="MT2-TRACE-REPLAY-PIPELINE",
            total_traces=len(stages),
            enriched_count=len(stages),
            replayable_count=replayable_count,
            not_replayable_count=len(stages) - replayable_count,
            pipeline_stages=stages,
            proved_at=_iso_now(),
        )

    def emit(self, record: TraceReplayPipelineRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "lace2_trace_replay_pipeline_proof.json"
        out_path.write_text(
            json.dumps({
                "pipeline_id": record.pipeline_id,
                "selected_tranche": record.selected_tranche,
                "total_traces": record.total_traces,
                "enriched_count": record.enriched_count,
                "replayable_count": record.replayable_count,
                "not_replayable_count": record.not_replayable_count,
                "pipeline_stages": [asdict(s) for s in record.pipeline_stages],
                "proved_at": record.proved_at,
            }, indent=2),
            encoding="utf-8",
        )
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["PipelineStageResult", "TraceReplayPipelineRecord", "TraceReplayPipelineRunner"]
