"""Phase7TerminalCloseoutV1: terminal closeout assembly for Phase 7."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from framework.phase6_closeout_ratifier_v1 import Phase6CloseoutResultV1
from framework.phase7_promotion_v1 import Phase7PromotionResultV1
from framework.promotion_gate_ratifier_v1 import PromotionGateResultV1
from framework.real_telemetry_ingestion_v1 import TelemetryIngestionResultV1


@dataclass
class Phase7TerminalCloseoutResultV1:
    phase_id: str
    package_id: str
    phase6_closed: bool
    promotion_ready: bool
    promotion_gate_cleared: bool
    terminal_closeout_ready: bool
    blockers_remaining: List[str]
    terminal_summary: Dict[str, Any]
    escalation_status: str
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "package_id": self.package_id,
            "phase6_closed": self.phase6_closed,
            "promotion_ready": self.promotion_ready,
            "promotion_gate_cleared": self.promotion_gate_cleared,
            "terminal_closeout_ready": self.terminal_closeout_ready,
            "blockers_remaining": self.blockers_remaining,
            "terminal_summary": self.terminal_summary,
            "escalation_status": self.escalation_status,
            "generated_at": self.generated_at,
        }


class Phase7TerminalCloseoutV1:
    """Bundle all Phase 7 closeout surfaces into a terminal closeout record."""

    PHASE_ID = "phase_7"

    def assemble(
        self,
        package_id: str,
        phase6_closeout: Phase6CloseoutResultV1,
        promotion_result: Phase7PromotionResultV1,
        gate_result: PromotionGateResultV1,
        telemetry: TelemetryIngestionResultV1,
        escalation_status: str = "NOT_ESCALATED",
        closing_notes: Optional[List[str]] = None,
    ) -> Phase7TerminalCloseoutResultV1:
        # Aggregate all blockers
        all_blockers: List[str] = list(gate_result.blockers_remaining)
        if phase6_closeout.blockers_remaining:
            for b in phase6_closeout.blockers_remaining:
                if b not in all_blockers:
                    all_blockers.append(b)

        terminal_closeout_ready = (
            phase6_closeout.phase6_closed
            and promotion_result.promotion_ready
            and gate_result.promotion_gate_cleared
        )

        terminal_summary: Dict[str, Any] = {
            "phase6_closed": phase6_closeout.phase6_closed,
            "phase6_blockers_remaining": phase6_closeout.blockers_remaining,
            "promotion_ready": promotion_result.promotion_ready,
            "promotion_gate_cleared": gate_result.promotion_gate_cleared,
            "telemetry_complete": telemetry.telemetry_complete,
            "ledger_entries_seen": telemetry.ledger_entries_seen,
            "real_artifacts_seen": telemetry.real_artifacts_seen,
            "gate_readiness_summary": gate_result.readiness_summary,
        }
        if closing_notes:
            terminal_summary["closing_notes"] = closing_notes

        return Phase7TerminalCloseoutResultV1(
            phase_id=self.PHASE_ID,
            package_id=package_id,
            phase6_closed=phase6_closeout.phase6_closed,
            promotion_ready=promotion_result.promotion_ready,
            promotion_gate_cleared=gate_result.promotion_gate_cleared,
            terminal_closeout_ready=terminal_closeout_ready,
            blockers_remaining=all_blockers,
            terminal_summary=terminal_summary,
            escalation_status=escalation_status,
        )
