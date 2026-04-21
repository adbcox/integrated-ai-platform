"""Phase7PromotionV1: assemble promotion-readiness decision for Phase 7."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from framework.phase6_closeout_ratifier_v1 import Phase6CloseoutResultV1
from framework.local_autonomy_telemetry_bridge_v1 import TelemetryEvidenceSummaryV1
from framework.regression_summary_v1 import RegressionSummaryV1


@dataclass
class Phase7PromotionResultV1:
    phase_id: str
    package_id: str
    promotion_ready: bool
    promotion_blockers: List[str]
    promotion_summary: Dict[str, Any]
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "package_id": self.package_id,
            "promotion_ready": self.promotion_ready,
            "promotion_blockers": self.promotion_blockers,
            "promotion_summary": self.promotion_summary,
            "generated_at": self.generated_at,
        }


class Phase7PromotionV1:
    """Evaluate promotion readiness for Phase 7 from Phase 6 closeout + autonomy evidence."""

    PHASE_ID = "phase_7"

    def evaluate(
        self,
        package_id: str,
        phase6_closeout: Phase6CloseoutResultV1,
        telemetry_evidence: TelemetryEvidenceSummaryV1,
        regression_summary: RegressionSummaryV1,
        additional_notes: Optional[List[str]] = None,
    ) -> Phase7PromotionResultV1:
        promotion_blockers: List[str] = []

        if not phase6_closeout.phase6_closed:
            for b in phase6_closeout.blockers_remaining:
                promotion_blockers.append(f"phase6_not_closed: {b}")

        if not telemetry_evidence.routine_local_execution_ready:
            promotion_blockers.append(
                "routine_local_execution_ready=False; local-first path not established"
            )

        if not telemetry_evidence.first_pass_success_signal:
            promotion_blockers.append("first_pass_success_signal not met")

        if not telemetry_evidence.artifact_completeness_signal:
            promotion_blockers.append("artifact_completeness_signal not met")

        if regression_summary.pass_rate < 0.75:
            promotion_blockers.append(
                f"regression_pass_rate {regression_summary.pass_rate:.2f} < 0.75"
            )

        promotion_ready = len(promotion_blockers) == 0

        promotion_summary: Dict[str, Any] = {
            "phase6_closed": phase6_closeout.phase6_closed,
            "routine_local_execution_ready": telemetry_evidence.routine_local_execution_ready,
            "first_pass_success_signal": telemetry_evidence.first_pass_success_signal,
            "artifact_completeness_signal": telemetry_evidence.artifact_completeness_signal,
            "regression_pass_rate": regression_summary.pass_rate,
            "regression_cases_run": regression_summary.regression_cases_run,
            "evidence_gaps": telemetry_evidence.evidence_gaps,
        }
        if additional_notes:
            promotion_summary["notes"] = additional_notes

        return Phase7PromotionResultV1(
            phase_id=self.PHASE_ID,
            package_id=package_id,
            promotion_ready=promotion_ready,
            promotion_blockers=promotion_blockers,
            promotion_summary=promotion_summary,
        )
