"""LACE1-P7-REPLAY-RERUN-SEAM-1: replay eligibility decision surface from EnrichedTrace."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from framework.execution_trace_enricher import EnrichedTrace

assert "outcome_class" in EnrichedTrace.__dataclass_fields__, "INTERFACE MISMATCH: EnrichedTrace.outcome_class"
assert "retry_count" in EnrichedTrace.__dataclass_fields__, "INTERFACE MISMATCH: EnrichedTrace.retry_count"
assert "file_change_count" in EnrichedTrace.__dataclass_fields__, "INTERFACE MISMATCH: EnrichedTrace.file_change_count"
assert "source_result_id" in EnrichedTrace.__dataclass_fields__, "INTERFACE MISMATCH: EnrichedTrace.source_result_id"

_REPLAYABLE_OUTCOME_CLASSES = {"failure", "partial"}
_MAX_RETRY_FOR_REPLAY = 2


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


@dataclass(frozen=True)
class ReplaySpec:
    spec_id: str
    source_trace_id: str
    replayable: bool
    not_replayable_reason: Optional[str]
    task_description: str
    target_files: List[str]
    replay_priority: str     # "high"|"medium"|"low"
    generated_at: str


class ReplayGate:
    """Evaluates replay eligibility from an EnrichedTrace."""

    def evaluate(
        self,
        trace: EnrichedTrace,
        *,
        task_description: str = "",
        target_files: Optional[List[str]] = None,
    ) -> ReplaySpec:
        if target_files is None:
            target_files = []

        replayable = (
            trace.outcome_class in _REPLAYABLE_OUTCOME_CLASSES
            and trace.retry_count <= _MAX_RETRY_FOR_REPLAY
        )

        if not replayable:
            if trace.outcome_class not in _REPLAYABLE_OUTCOME_CLASSES:
                reason = f"outcome_class={trace.outcome_class!r} is not replayable"
            else:
                reason = f"retry_count={trace.retry_count} exceeds max={_MAX_RETRY_FOR_REPLAY}"
        else:
            reason = None

        if trace.retry_count == 0:
            priority = "high"
        elif trace.retry_count == 1:
            priority = "medium"
        else:
            priority = "low"

        spec_id = f"REPLAY-{trace.trace_id[:20]}-{_ts()}"
        return ReplaySpec(
            spec_id=spec_id,
            source_trace_id=trace.trace_id,
            replayable=replayable,
            not_replayable_reason=reason,
            task_description=task_description,
            target_files=list(target_files),
            replay_priority=priority,
            generated_at=_iso_now(),
        )

    def emit(self, spec: ReplaySpec, artifact_dir: Path) -> str:
        artifact_dir = Path(artifact_dir)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        out_path = artifact_dir / f"{spec.spec_id}.json"
        out_path.write_text(
            json.dumps(
                {
                    "spec_id": spec.spec_id,
                    "source_trace_id": spec.source_trace_id,
                    "replayable": spec.replayable,
                    "not_replayable_reason": spec.not_replayable_reason,
                    "task_description": spec.task_description,
                    "target_files": spec.target_files,
                    "replay_priority": spec.replay_priority,
                    "generated_at": spec.generated_at,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return str(out_path)


__all__ = ["ReplaySpec", "ReplayGate"]
