"""LACE2-P6-LIVE-REPLAY-PROOF-SEAM-1: prove ReplayGate on bounded LACE2 enriched traces."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from framework.replay_gate import ReplayGate, ReplaySpec
from framework.execution_trace_enricher import EnrichedTrace, ExecutionTraceEnricher, _FAILED_STATES
from framework.execution_trace_result_schema import ExecutionTraceResult

assert "replayable" in ReplaySpec.__dataclass_fields__, "INTERFACE MISMATCH: ReplaySpec.replayable"
assert "replay_priority" in ReplaySpec.__dataclass_fields__, "INTERFACE MISMATCH: ReplaySpec.replay_priority"
assert "not_replayable_reason" in ReplaySpec.__dataclass_fields__, \
    "INTERFACE MISMATCH: ReplaySpec.not_replayable_reason"
assert "outcome_class" in EnrichedTrace.__dataclass_fields__, "INTERFACE MISMATCH: EnrichedTrace.outcome_class"
assert "retry_count" in EnrichedTrace.__dataclass_fields__, "INTERFACE MISMATCH: EnrichedTrace.retry_count"

_FAILED_STATE_ONE = next(iter(_FAILED_STATES))

_LACE2_TRACE_DEFS = [
    ("LACE2-DECOMP",       "complete",        ["framework/scheduler.py"],   0),
    ("LACE2-RETRIEVAL",    "complete",        ["framework/worker_runtime.py"], 0),
    ("LACE2-REPAIR-RETRY", "complete",        ["framework/repair_policy_gate.py"], 1),
    ("LACE2-REPAIR-FAIL",  _FAILED_STATE_ONE, [], 0),
    ("LACE2-PARTIAL",      "partial",         ["framework/scheduler.py"], 0),
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass(frozen=True)
class ReplayProofRow:
    trace_id: str
    outcome_class: str
    retry_count: int
    replayable: bool
    replay_priority: str
    not_replayable_reason: Optional[str]


@dataclass
class ReplayProofRecord:
    proof_id: str
    total_traces: int
    replayable_count: int
    not_replayable_count: int
    priority_distribution: Dict[str, int]
    rows: List[ReplayProofRow]
    proved_at: str
    artifact_path: Optional[str] = None


class ReplayProofRunner:
    """Drives ReplayGate on real LACE2 enriched traces."""

    def run(self) -> ReplayProofRecord:
        enricher = ExecutionTraceEnricher()
        gate = ReplayGate()
        rows: List[ReplayProofRow] = []
        priority_dist: Dict[str, int] = {}

        for (rid, state, items, retry) in _LACE2_TRACE_DEFS:
            result = ExecutionTraceResult(
                result_id=rid,
                result_state=state,
                completed_trace_items=list(items),
            )
            trace: EnrichedTrace = enricher.enrich(result, retry_count=retry)
            spec: ReplaySpec = gate.evaluate(trace)

            priority_key = spec.replay_priority if spec.replayable else "n/a"
            priority_dist[priority_key] = priority_dist.get(priority_key, 0) + 1

            rows.append(ReplayProofRow(
                trace_id=rid,
                outcome_class=trace.outcome_class,
                retry_count=trace.retry_count,
                replayable=spec.replayable,
                replay_priority=priority_key,
                not_replayable_reason=spec.not_replayable_reason,
            ))

        replayable_count = sum(1 for r in rows if r.replayable)
        return ReplayProofRecord(
            proof_id=f"RPF-LACE2-{_ts()}",
            total_traces=len(rows),
            replayable_count=replayable_count,
            not_replayable_count=len(rows) - replayable_count,
            priority_distribution=priority_dist,
            rows=rows,
            proved_at=_iso_now(),
        )

    def emit(self, record: ReplayProofRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "replay_proof.json"
        out_path.write_text(
            json.dumps({
                "proof_id": record.proof_id,
                "total_traces": record.total_traces,
                "replayable_count": record.replayable_count,
                "not_replayable_count": record.not_replayable_count,
                "priority_distribution": record.priority_distribution,
                "rows": [asdict(r) for r in record.rows],
                "proved_at": record.proved_at,
            }, indent=2),
            encoding="utf-8",
        )
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["ReplayProofRow", "ReplayProofRecord", "ReplayProofRunner"]
