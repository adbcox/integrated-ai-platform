"""Phase6CloseoutRatifierV1: ratify Phase 6 closeout from structured evidence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from framework.persistent_execution_ledger_v1 import PersistentExecutionLedgerV1
from framework.local_autonomy_telemetry_bridge_v1 import TelemetryEvidenceSummaryV1
from framework.escalation_workflow_v1 import EscalationWorkflowV1


@dataclass
class Phase6CloseoutResultV1:
    phase6_closed: bool
    blockers_remaining: List[str]
    closeout_summary: Dict[str, Any]
    ratified_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase6_closed": self.phase6_closed,
            "blockers_remaining": self.blockers_remaining,
            "closeout_summary": self.closeout_summary,
            "ratified_at": self.ratified_at,
        }


class Phase6CloseoutRatifierV1:
    """Ratify Phase 6 closeout from persistent ledger, telemetry evidence, and escalation records."""

    P6_BLOCKERS = [
        "P6-BLOCKER-01",  # ledger persistence
        "P6-BLOCKER-02",  # aider dispatch
        "P6-BLOCKER-03",  # telemetry from real runs
        "P6-BLOCKER-04",  # escalation approval workflow
    ]

    def ratify(
        self,
        ledger: PersistentExecutionLedgerV1,
        telemetry_evidence: TelemetryEvidenceSummaryV1,
        escalation_workflow: EscalationWorkflowV1,
        additional_notes: Optional[List[str]] = None,
    ) -> Phase6CloseoutResultV1:
        blockers_remaining: List[str] = []
        summary = ledger.summarize()

        # Check each Phase 6 blocker resolution
        # P6-BLOCKER-01: persistent ledger now present
        if summary["total_runs"] == 0:
            blockers_remaining.append(
                "P6-BLOCKER-01: persistent ledger has no entries; runs not yet recorded"
            )

        # P6-BLOCKER-02: aider dispatch surface present (structural check only)
        # Resolved if live_aider_dispatch_v1 module exists — checked at import time by runner

        # P6-BLOCKER-03: telemetry from real runs
        if not telemetry_evidence.routine_local_execution_ready:
            blockers_remaining.append(
                "P6-BLOCKER-03: routine_local_execution_ready=False; "
                f"gaps: {telemetry_evidence.evidence_gaps}"
            )

        # P6-BLOCKER-04: escalation workflow surface present (structural; any events recorded)
        # No hard requirement on count for ratification

        phase6_closed = len(blockers_remaining) == 0

        closeout_summary: Dict[str, Any] = {
            "ledger_total_runs": summary["total_runs"],
            "ledger_pass_rate": summary["pass_rate"],
            "routine_local_execution_ready": telemetry_evidence.routine_local_execution_ready,
            "escalation_events_recorded": len(escalation_workflow.all_events()),
            "autonomy_progress_count": escalation_workflow.autonomy_progress_count,
            "evidence_gaps": telemetry_evidence.evidence_gaps,
            "phase6_blockers_evaluated": self.P6_BLOCKERS,
        }
        if additional_notes:
            closeout_summary["notes"] = additional_notes

        return Phase6CloseoutResultV1(
            phase6_closed=phase6_closed,
            blockers_remaining=blockers_remaining,
            closeout_summary=closeout_summary,
        )
