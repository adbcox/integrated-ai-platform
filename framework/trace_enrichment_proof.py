"""LACE2-P5-LIVE-TRACE-ENRICHMENT-WIRING-SEAM-1: wire ExecutionTraceEnricher on LACE2 proof-flow traces."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from framework.execution_trace_enricher import ExecutionTraceEnricher, EnrichedTrace, _FAILED_STATES
from framework.execution_trace_result_schema import ExecutionTraceResult

assert "result_id" in ExecutionTraceResult.__dataclass_fields__, "INTERFACE MISMATCH: ExecutionTraceResult.result_id"
assert "result_state" in ExecutionTraceResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: ExecutionTraceResult.result_state"
assert "completed_trace_items" in ExecutionTraceResult.__dataclass_fields__, \
    "INTERFACE MISMATCH: ExecutionTraceResult.completed_trace_items"
assert "outcome_class" in EnrichedTrace.__dataclass_fields__, "INTERFACE MISMATCH: EnrichedTrace.outcome_class"
assert "retry_count" in EnrichedTrace.__dataclass_fields__, "INTERFACE MISMATCH: EnrichedTrace.retry_count"
assert "file_change_count" in EnrichedTrace.__dataclass_fields__, \
    "INTERFACE MISMATCH: EnrichedTrace.file_change_count"

# _FAILED_STATES must be defined (already asserted importable above)
assert isinstance(_FAILED_STATES, (set, frozenset)), "INTERFACE MISMATCH: _FAILED_STATES not a set"

_FAILED_STATE_ONE = next(iter(_FAILED_STATES))  # use a real value from the actual set

_LACE2_PROOF_TRACES = [
    # (result_id, result_state, completed_items, notes, retry_count)
    ("LACE2-DECOMP",       "complete",         ["framework/scheduler.py"],                          "",                  0),
    ("LACE2-RETRIEVAL",    "complete",         ["framework/worker_runtime.py", "framework/job_schema.py"], "",            0),
    ("LACE2-REPAIR-RETRY", "complete",         ["framework/repair_policy_gate.py"],                 "",                  1),
    ("LACE2-REPAIR-FAIL",  _FAILED_STATE_ONE,  [],                                                  "validation error",  0),
    ("LACE2-PARTIAL",      "partial",          ["framework/scheduler.py"],                          "",                  0),
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass
class TraceEnrichmentProofRecord:
    proof_id: str
    input_trace_count: int
    enriched_traces: List[dict]
    outcome_class_distribution: Dict[str, int]
    proved_at: str
    artifact_path: Optional[str] = None


class TraceEnrichmentProofRunner:
    """Enriches typed LACE2 proof-flow trace records using ExecutionTraceEnricher."""

    def run(self) -> TraceEnrichmentProofRecord:
        enricher = ExecutionTraceEnricher()
        enriched_dicts: List[dict] = []
        distribution: Dict[str, int] = {}

        for (rid, state, items, notes, retry) in _LACE2_PROOF_TRACES:
            result = ExecutionTraceResult(
                result_id=rid,
                result_state=state,
                completed_trace_items=list(items),
                notes=notes,
            )
            trace: EnrichedTrace = enricher.enrich(result, retry_count=retry)
            enriched_dicts.append(asdict(trace))
            distribution[trace.outcome_class] = distribution.get(trace.outcome_class, 0) + 1

        return TraceEnrichmentProofRecord(
            proof_id=f"TEP-LACE2-{_ts()}",
            input_trace_count=len(_LACE2_PROOF_TRACES),
            enriched_traces=enriched_dicts,
            outcome_class_distribution=distribution,
            proved_at=_iso_now(),
        )

    def emit(self, record: TraceEnrichmentProofRecord, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / "trace_enrichment_proof.json"
        out_path.write_text(
            json.dumps({
                "proof_id": record.proof_id,
                "input_trace_count": record.input_trace_count,
                "outcome_class_distribution": record.outcome_class_distribution,
                "enriched_traces": record.enriched_traces,
                "proved_at": record.proved_at,
            }, indent=2),
            encoding="utf-8",
        )
        record.artifact_path = str(out_path)
        return str(out_path)


__all__ = ["TraceEnrichmentProofRecord", "TraceEnrichmentProofRunner"]
