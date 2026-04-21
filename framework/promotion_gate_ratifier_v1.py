"""PromotionGateRatifierV1: ratify the Phase 7 promotion gate from live evidence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from framework.live_aider_proof_v1 import AiderProofResultV1, PROOF_MODE_LIVE, PROOF_MODE_DRY_RUN_ONLY
from framework.real_telemetry_ingestion_v1 import TelemetryIngestionResultV1
from framework.live_escalation_evidence_v1 import EscalationEvidenceSummaryV1
from framework.phase7_promotion_v1 import Phase7PromotionResultV1


@dataclass
class PromotionGateResultV1:
    promotion_gate_cleared: bool
    blockers_remaining: List[str]
    readiness_summary: Dict[str, Any]
    ratified_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "promotion_gate_cleared": self.promotion_gate_cleared,
            "blockers_remaining": self.blockers_remaining,
            "readiness_summary": self.readiness_summary,
            "ratified_at": self.ratified_at,
        }


class PromotionGateRatifierV1:
    """
    Ratify the Phase 7 promotion gate from live evidence surfaces.

    If live evidence is incomplete, returns partial/blocked truthfully.
    """

    def ratify(
        self,
        aider_proof: AiderProofResultV1,
        telemetry: TelemetryIngestionResultV1,
        escalation_evidence: EscalationEvidenceSummaryV1,
        promotion_result: Phase7PromotionResultV1,
        notes: Optional[List[str]] = None,
    ) -> PromotionGateResultV1:
        blockers: List[str] = []

        # 1. Aider dispatch proof — live preferred, dry-run accepted with note
        if not aider_proof.live_dispatch_attempted:
            blockers.append(
                "aider_proof: live dispatch not attempted; dry_run_only proof present"
            )
        elif aider_proof.live_dispatch_attempted and not aider_proof.live_dispatch_succeeded:
            blockers.append(
                f"aider_proof: live dispatch attempted but not succeeded "
                f"(mode={aider_proof.dispatch_mode}, reason={aider_proof.failure_reason!r})"
            )
        # If live succeeded — gate cleared for this dimension

        # 2. Telemetry completeness
        if not telemetry.telemetry_complete:
            for gap in telemetry.evidence_gaps:
                blockers.append(f"telemetry: {gap}")

        # 3. Escalation accounting invariant
        if not escalation_evidence.local_autonomy_progress_preserved:
            for gap in escalation_evidence.evidence_gaps:
                blockers.append(f"escalation_evidence: {gap}")

        # 4. Promotion decision
        if not promotion_result.promotion_ready:
            for b in promotion_result.promotion_blockers:
                blockers.append(f"promotion: {b}")

        promotion_gate_cleared = len(blockers) == 0

        readiness_summary: Dict[str, Any] = {
            "aider_proof_dispatch_mode": aider_proof.dispatch_mode,
            "aider_live_succeeded": aider_proof.live_dispatch_succeeded,
            "telemetry_complete": telemetry.telemetry_complete,
            "ledger_entries_seen": telemetry.ledger_entries_seen,
            "real_artifacts_seen": telemetry.real_artifacts_seen,
            "local_autonomy_preserved": escalation_evidence.local_autonomy_progress_preserved,
            "promotion_ready": promotion_result.promotion_ready,
            "promotion_blockers_count": len(promotion_result.promotion_blockers),
        }
        if notes:
            readiness_summary["notes"] = notes

        return PromotionGateResultV1(
            promotion_gate_cleared=promotion_gate_cleared,
            blockers_remaining=blockers,
            readiness_summary=readiness_summary,
        )
