"""Phase 5 readiness evaluator for Phase 4 self-sufficiency uplift (P4-01)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ReadinessDimensionResultV1:
    dimension: str
    met: bool
    evidence: str
    gap: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "met": self.met,
            "evidence": self.evidence,
            "gap": self.gap,
        }


@dataclass
class Phase5ReadinessResultV1:
    ready: bool
    blocking_gaps: List[str]
    evidence_summary: Dict[str, bool]
    dimension_results: List[ReadinessDimensionResultV1] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ready": self.ready,
            "blocking_gaps": self.blocking_gaps,
            "evidence_summary": self.evidence_summary,
            "dimension_results": [d.to_dict() for d in self.dimension_results],
        }


class Phase5ReadinessEvaluatorV1:
    """Evaluates whether the Phase 4 uplift surfaces meet Phase 5 entry criteria."""

    REQUIRED_DIMENSIONS = [
        "artifact_completeness",
        "validation_pass_rate",
        "escalation_accounting",
        "first_pass_success_signal",
        "retry_discipline_signal",
    ]

    def evaluate(
        self,
        artifact_complete: bool,
        validation_pass_rate: float,
        escalation_status_present: bool,
        first_pass_successes: int,
        total_cases: int,
        retries_within_budget: bool,
        notes: Optional[List[str]] = None,
    ) -> Phase5ReadinessResultV1:
        dims: List[ReadinessDimensionResultV1] = []
        blocking_gaps: List[str] = []

        # Dimension 1: artifact_completeness
        d1 = ReadinessDimensionResultV1(
            dimension="artifact_completeness",
            met=artifact_complete,
            evidence="artifact emitted and all required fields present" if artifact_complete
                     else "artifact missing or incomplete",
            gap=None if artifact_complete else "artifact fields incomplete",
        )
        dims.append(d1)
        if not d1.met:
            blocking_gaps.append(d1.gap)  # type: ignore[arg-type]

        # Dimension 2: validation_pass_rate
        rate_ok = validation_pass_rate >= 0.75
        d2 = ReadinessDimensionResultV1(
            dimension="validation_pass_rate",
            met=rate_ok,
            evidence=f"pass_rate={validation_pass_rate:.2f}",
            gap=None if rate_ok else f"pass_rate {validation_pass_rate:.2f} < 0.75 threshold",
        )
        dims.append(d2)
        if not d2.met:
            blocking_gaps.append(d2.gap)  # type: ignore[arg-type]

        # Dimension 3: escalation_accounting
        d3 = ReadinessDimensionResultV1(
            dimension="escalation_accounting",
            met=escalation_status_present,
            evidence="escalation_status field present in all outputs" if escalation_status_present
                     else "escalation_status missing from one or more outputs",
            gap=None if escalation_status_present else "escalation_status not explicitly reported",
        )
        dims.append(d3)
        if not d3.met:
            blocking_gaps.append(d3.gap)  # type: ignore[arg-type]

        # Dimension 4: first_pass_success_signal
        fp_rate = first_pass_successes / total_cases if total_cases > 0 else 0.0
        fp_ok = fp_rate >= 0.5
        d4 = ReadinessDimensionResultV1(
            dimension="first_pass_success_signal",
            met=fp_ok,
            evidence=f"{first_pass_successes}/{total_cases} first-pass successes (rate={fp_rate:.2f})",
            gap=None if fp_ok else f"first-pass rate {fp_rate:.2f} < 0.50 threshold",
        )
        dims.append(d4)
        if not d4.met:
            blocking_gaps.append(d4.gap)  # type: ignore[arg-type]

        # Dimension 5: retry_discipline_signal
        d5 = ReadinessDimensionResultV1(
            dimension="retry_discipline_signal",
            met=retries_within_budget,
            evidence="all retries within declared retry_budget" if retries_within_budget
                     else "one or more tasks exceeded retry_budget",
            gap=None if retries_within_budget else "retry budget exceeded",
        )
        dims.append(d5)
        if not d5.met:
            blocking_gaps.append(d5.gap)  # type: ignore[arg-type]

        evidence_summary = {d.dimension: d.met for d in dims}
        ready = len(blocking_gaps) == 0

        return Phase5ReadinessResultV1(
            ready=ready,
            blocking_gaps=blocking_gaps,
            evidence_summary=evidence_summary,
            dimension_results=dims,
        )
