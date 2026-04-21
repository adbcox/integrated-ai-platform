"""EscalationRecordV1: typed escalation record that enforces local-autonomy accounting."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class EscalationRecordV1:
    run_id: str
    package_id: str
    escalation_requested: bool
    escalation_approved: bool
    escalation_reason: str
    # INVARIANT: Claude rescue never counts as local autonomy progress.
    # This field must always be False when executor is Claude.
    counts_as_local_autonomy_progress: bool
    executor: str
    recorded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Enforce the invariant: Claude executor runs never count as progress.
        if self.executor.lower() in {"claude", "claude_code", "remote_assist"}:
            if self.counts_as_local_autonomy_progress:
                raise ValueError(
                    f"EscalationRecordV1: executor '{self.executor}' is a Claude/remote executor; "
                    "counts_as_local_autonomy_progress must be False."
                )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "package_id": self.package_id,
            "escalation_requested": self.escalation_requested,
            "escalation_approved": self.escalation_approved,
            "escalation_reason": self.escalation_reason,
            "counts_as_local_autonomy_progress": self.counts_as_local_autonomy_progress,
            "executor": self.executor,
            "recorded_at": self.recorded_at,
            "notes": self.notes,
        }


class EscalationRegistryV1:
    """Registry of escalation records for a session."""

    def __init__(self) -> None:
        self._records: List[EscalationRecordV1] = []

    def record(
        self,
        run_id: str,
        package_id: str,
        escalation_requested: bool,
        escalation_approved: bool,
        escalation_reason: str,
        executor: str,
        notes: Optional[List[str]] = None,
    ) -> EscalationRecordV1:
        # counts_as_local_autonomy_progress is True only for non-Claude local executors
        is_claude = executor.lower() in {"claude", "claude_code", "remote_assist"}
        counts = not is_claude and not escalation_requested

        rec = EscalationRecordV1(
            run_id=run_id,
            package_id=package_id,
            escalation_requested=escalation_requested,
            escalation_approved=escalation_approved,
            escalation_reason=escalation_reason,
            counts_as_local_autonomy_progress=counts,
            executor=executor,
            notes=notes or [],
        )
        self._records.append(rec)
        return rec

    def all_records(self) -> List[EscalationRecordV1]:
        return list(self._records)

    @property
    def escalated_count(self) -> int:
        return sum(1 for r in self._records if r.escalation_requested)

    @property
    def autonomy_progress_count(self) -> int:
        return sum(1 for r in self._records if r.counts_as_local_autonomy_progress)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_records": len(self._records),
            "escalated_count": self.escalated_count,
            "autonomy_progress_count": self.autonomy_progress_count,
            "records": [r.to_dict() for r in self._records],
        }
