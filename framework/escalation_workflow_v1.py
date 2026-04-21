"""EscalationWorkflowV1: explicit escalation workflow with local-autonomy accounting."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

CLAUDE_EXECUTORS = frozenset({"claude", "claude_code", "remote_assist"})
APPROVER_HUMAN = "human"
APPROVER_POLICY = "policy"
APPROVER_AUTO = "auto"


@dataclass
class EscalationEventV1:
    run_id: str
    package_id: str
    escalation_requested: bool
    escalation_reason: str
    escalation_approved: bool
    approver_type: str
    executor: str
    # Invariant: Claude/remote assist never counts as local autonomy progress
    counts_as_local_autonomy_progress: bool
    recorded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.executor.lower() in CLAUDE_EXECUTORS and self.counts_as_local_autonomy_progress:
            raise ValueError(
                f"EscalationEventV1: executor '{self.executor}' is Claude/remote; "
                "counts_as_local_autonomy_progress must be False."
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "package_id": self.package_id,
            "escalation_requested": self.escalation_requested,
            "escalation_reason": self.escalation_reason,
            "escalation_approved": self.escalation_approved,
            "approver_type": self.approver_type,
            "executor": self.executor,
            "counts_as_local_autonomy_progress": self.counts_as_local_autonomy_progress,
            "recorded_at": self.recorded_at,
            "notes": self.notes,
        }


@dataclass
class EscalationDecisionV1:
    escalation_warranted: bool
    reasons: List[str]
    recommended_approver: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "escalation_warranted": self.escalation_warranted,
            "reasons": self.reasons,
            "recommended_approver": self.recommended_approver,
        }


class EscalationWorkflowV1:
    """Manage escalation events with explicit local-autonomy accounting."""

    def __init__(self) -> None:
        self._events: List[EscalationEventV1] = []

    def record_event(
        self,
        run_id: str,
        package_id: str,
        escalation_requested: bool,
        escalation_reason: str,
        escalation_approved: bool,
        executor: str,
        approver_type: str = APPROVER_AUTO,
        notes: Optional[List[str]] = None,
    ) -> EscalationEventV1:
        is_claude = executor.lower() in CLAUDE_EXECUTORS
        counts = not is_claude and not escalation_requested

        event = EscalationEventV1(
            run_id=run_id,
            package_id=package_id,
            escalation_requested=escalation_requested,
            escalation_reason=escalation_reason,
            escalation_approved=escalation_approved,
            approver_type=approver_type,
            executor=executor,
            counts_as_local_autonomy_progress=counts,
            notes=notes or [],
        )
        self._events.append(event)
        return event

    def evaluate(
        self,
        failure_count: int,
        retry_budget_remaining: int,
        task_complexity: str = "medium",
    ) -> EscalationDecisionV1:
        reasons: List[str] = []
        warranted = False

        if failure_count >= 3:
            warranted = True
            reasons.append(f"failure_count={failure_count} >= 3")
        if retry_budget_remaining <= 0:
            warranted = True
            reasons.append("retry_budget exhausted")
        if task_complexity == "high" and failure_count >= 1:
            warranted = True
            reasons.append(f"high complexity task with {failure_count} failure(s)")

        recommended = APPROVER_HUMAN if warranted else APPROVER_AUTO
        return EscalationDecisionV1(
            escalation_warranted=warranted,
            reasons=reasons,
            recommended_approver=recommended,
        )

    def all_events(self) -> List[EscalationEventV1]:
        return list(self._events)

    @property
    def escalated_count(self) -> int:
        return sum(1 for e in self._events if e.escalation_requested)

    @property
    def autonomy_progress_count(self) -> int:
        return sum(1 for e in self._events if e.counts_as_local_autonomy_progress)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_events": len(self._events),
            "escalated_count": self.escalated_count,
            "autonomy_progress_count": self.autonomy_progress_count,
            "events": [e.to_dict() for e in self._events],
        }
