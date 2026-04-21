"""QualificationReadinessEvaluatorV1: evaluate qualification readiness from evidence."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class QualificationReadinessResultV1:
    artifact_completeness: bool
    validation_pass_rate: float
    escalation_accounting: bool
    readiness_ready: bool
    blocking_gaps: List[str]
    evidence_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_completeness": self.artifact_completeness,
            "validation_pass_rate": self.validation_pass_rate,
            "escalation_accounting": self.escalation_accounting,
            "readiness_ready": self.readiness_ready,
            "blocking_gaps": self.blocking_gaps,
            "evidence_summary": self.evidence_summary,
        }


class QualificationReadinessEvaluatorV1:
    """Evaluate whether a package meets the qualification readiness threshold."""

    PASS_RATE_THRESHOLD = 0.75

    def evaluate(
        self,
        artifact_complete: bool,
        validation_pass_rate: float,
        escalation_status_present: bool,
        evidence_notes: Optional[List[str]] = None,
    ) -> QualificationReadinessResultV1:
        blocking_gaps: List[str] = []

        if not artifact_complete:
            blocking_gaps.append("artifact_completeness: required fields absent or null")

        if validation_pass_rate < self.PASS_RATE_THRESHOLD:
            blocking_gaps.append(
                f"validation_pass_rate: {validation_pass_rate:.2f} < {self.PASS_RATE_THRESHOLD}"
            )

        if not escalation_status_present:
            blocking_gaps.append(
                "escalation_accounting: escalation_status absent from outputs"
            )

        readiness_ready = len(blocking_gaps) == 0

        evidence_summary: Dict[str, Any] = {
            "artifact_complete": artifact_complete,
            "validation_pass_rate": validation_pass_rate,
            "escalation_status_present": escalation_status_present,
            "pass_rate_threshold": self.PASS_RATE_THRESHOLD,
        }
        if evidence_notes:
            evidence_summary["notes"] = evidence_notes

        return QualificationReadinessResultV1(
            artifact_completeness=artifact_complete,
            validation_pass_rate=validation_pass_rate,
            escalation_accounting=escalation_status_present,
            readiness_ready=readiness_ready,
            blocking_gaps=blocking_gaps,
            evidence_summary=evidence_summary,
        )
