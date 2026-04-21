"""Phase5CloseoutV1: assemble a structured Phase 5 closeout record."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from framework.unified_validation_artifact_v1 import UnifiedValidationArtifactV1
from framework.qualification_readiness_v1 import QualificationReadinessResultV1
from framework.local_autonomy_gate_v1 import LocalAutonomyGateResultV1
from framework.regression_summary_v1 import RegressionSummaryV1


@dataclass
class Phase5CloseoutRecordV1:
    phase_id: str
    package_id: str
    generated_at: str
    unified_artifact: UnifiedValidationArtifactV1
    qualification_result: QualificationReadinessResultV1
    autonomy_gate_result: LocalAutonomyGateResultV1
    regression_summary: RegressionSummaryV1
    escalation_status: str
    promotion_readiness_ready: bool
    closing_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase_id": self.phase_id,
            "package_id": self.package_id,
            "generated_at": self.generated_at,
            "unified_artifact": self.unified_artifact.to_dict(),
            "qualification_result": self.qualification_result.to_dict(),
            "autonomy_gate_result": self.autonomy_gate_result.to_dict(),
            "regression_summary": self.regression_summary.to_dict(),
            "escalation_status": self.escalation_status,
            "promotion_readiness_ready": self.promotion_readiness_ready,
            "closing_notes": self.closing_notes,
        }


class Phase5CloseoutV1:
    """Assemble a Phase 5 closeout record from component results."""

    PHASE_ID = "phase_5"

    def assemble(
        self,
        package_id: str,
        unified_artifact: UnifiedValidationArtifactV1,
        qualification_result: QualificationReadinessResultV1,
        autonomy_gate_result: LocalAutonomyGateResultV1,
        regression_summary: RegressionSummaryV1,
        escalation_status: str = "NOT_ESCALATED",
        closing_notes: Optional[List[str]] = None,
    ) -> Phase5CloseoutRecordV1:
        promotion_readiness_ready = (
            qualification_result.readiness_ready
            and autonomy_gate_result.gate_passed
            and unified_artifact.all_passed
        )

        return Phase5CloseoutRecordV1(
            phase_id=self.PHASE_ID,
            package_id=package_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            unified_artifact=unified_artifact,
            qualification_result=qualification_result,
            autonomy_gate_result=autonomy_gate_result,
            regression_summary=regression_summary,
            escalation_status=escalation_status,
            promotion_readiness_ready=promotion_readiness_ready,
            closing_notes=closing_notes or [],
        )
