"""Phase6TransitionV1: assemble a structured Phase 6 local-first transition result."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from framework.local_execution_ledger_v1 import LocalExecutionLedgerV1
from framework.aider_execution_adapter_v1 import AiderExecutionAdapterV1, AiderHandoffRecordV1
from framework.local_autonomy_evidence_bridge_v1 import LocalAutonomyEvidenceSummaryV1
from framework.escalation_record_v1 import EscalationRegistryV1


@dataclass
class Phase6TransitionResultV1:
    phase_id: str
    package_id: str
    generated_at: str
    ledger_summary: Dict[str, Any]
    aider_handoff: AiderHandoffRecordV1
    autonomy_evidence: LocalAutonomyEvidenceSummaryV1
    escalation_registry_summary: Dict[str, Any]
    escalation_status: str
    transition_ready: bool
    closing_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "package_id": self.package_id,
            "generated_at": self.generated_at,
            "ledger_summary": self.ledger_summary,
            "aider_handoff": self.aider_handoff.to_dict(),
            "autonomy_evidence": self.autonomy_evidence.to_dict(),
            "escalation_registry_summary": self.escalation_registry_summary,
            "escalation_status": self.escalation_status,
            "transition_ready": self.transition_ready,
            "closing_notes": self.closing_notes,
        }


class Phase6TransitionV1:
    """Assemble a Phase 6 local-first transition result from component surfaces."""

    PHASE_ID = "phase_6"

    def assemble(
        self,
        package_id: str,
        ledger: LocalExecutionLedgerV1,
        aider_handoff: AiderHandoffRecordV1,
        autonomy_evidence: LocalAutonomyEvidenceSummaryV1,
        escalation_registry: EscalationRegistryV1,
        escalation_status: str = "NOT_ESCALATED",
        closing_notes: Optional[List[str]] = None,
    ) -> Phase6TransitionResultV1:
        adapter = AiderExecutionAdapterV1()
        transition_ready = (
            autonomy_evidence.routine_local_execution_ready
            and adapter.is_ready(aider_handoff)
        )

        return Phase6TransitionResultV1(
            phase_id=self.PHASE_ID,
            package_id=package_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            ledger_summary=ledger.to_dict(),
            aider_handoff=aider_handoff,
            autonomy_evidence=autonomy_evidence,
            escalation_registry_summary=escalation_registry.to_dict(),
            escalation_status=escalation_status,
            transition_ready=transition_ready,
            closing_notes=closing_notes or [],
        )
