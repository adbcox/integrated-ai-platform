"""LiveEscalationEvidenceV1: escalation evidence surface from actual run records."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from framework.escalation_workflow_v1 import EscalationWorkflowV1, EscalationEventV1

CLAUDE_EXECUTORS = frozenset({"claude", "claude_code", "remote_assist"})


@dataclass
class EscalationEvidenceSummaryV1:
    escalation_events_seen: int
    escalation_required_events: int
    remote_assist_events: int
    local_autonomy_progress_preserved: bool
    evidence_gaps: List[str]
    recorded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "escalation_events_seen": self.escalation_events_seen,
            "escalation_required_events": self.escalation_required_events,
            "remote_assist_events": self.remote_assist_events,
            "local_autonomy_progress_preserved": self.local_autonomy_progress_preserved,
            "evidence_gaps": self.evidence_gaps,
            "recorded_at": self.recorded_at,
            "detail": self.detail,
        }


class LiveEscalationEvidenceV1:
    """
    Derive escalation evidence from actual run records in the EscalationWorkflowV1.

    Enforces: Claude/remote assist cannot count as local autonomy progress.
    """

    def derive(
        self,
        workflow: EscalationWorkflowV1,
        notes: Optional[List[str]] = None,
    ) -> EscalationEvidenceSummaryV1:
        events = workflow.all_events()
        evidence_gaps: List[str] = []

        escalation_required = [e for e in events if e.escalation_requested]
        remote_assist = [e for e in events if e.executor.lower() in CLAUDE_EXECUTORS]

        # Verify invariant: no remote/Claude event marks local autonomy progress
        violations = [
            e for e in remote_assist
            if e.counts_as_local_autonomy_progress
        ]
        local_autonomy_preserved = len(violations) == 0
        if not local_autonomy_preserved:
            for v in violations:
                evidence_gaps.append(
                    f"INVARIANT VIOLATION: run_id={v.run_id!r}, executor={v.executor!r} "
                    "marked counts_as_local_autonomy_progress=True"
                )

        if len(events) == 0:
            evidence_gaps.append("no escalation events recorded in workflow")

        detail: Dict[str, Any] = {
            "total_events": len(events),
            "escalation_required_count": len(escalation_required),
            "remote_assist_count": len(remote_assist),
            "autonomy_progress_count": workflow.autonomy_progress_count,
            "invariant_violations": len(violations),
        }
        if notes:
            detail["notes"] = notes

        return EscalationEvidenceSummaryV1(
            escalation_events_seen=len(events),
            escalation_required_events=len(escalation_required),
            remote_assist_events=len(remote_assist),
            local_autonomy_progress_preserved=local_autonomy_preserved,
            evidence_gaps=evidence_gaps,
            detail=detail,
        )
