"""LocalAutonomyGateEvaluatorV1: evaluate local autonomy gate from execution signals."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LocalAutonomyGateResultV1:
    gate_passed: bool
    gate_reasons: List[str]
    gate_blockers: List[str]
    signal_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_passed": self.gate_passed,
            "gate_reasons": self.gate_reasons,
            "gate_blockers": self.gate_blockers,
            "signal_summary": self.signal_summary,
        }


class LocalAutonomyGateEvaluatorV1:
    """Evaluate whether the local autonomy gate is cleared based on execution signals."""

    FIRST_PASS_THRESHOLD = 0.50
    MAX_ESCALATION_RATE = 0.25

    def evaluate(
        self,
        first_pass_success_rate: float,
        retries_within_budget: bool,
        escalation_rate: float,
        artifact_completeness_signal: bool,
        notes: Optional[List[str]] = None,
    ) -> LocalAutonomyGateResultV1:
        gate_blockers: List[str] = []
        gate_reasons: List[str] = []

        # First-pass success signal
        if first_pass_success_rate >= self.FIRST_PASS_THRESHOLD:
            gate_reasons.append(
                f"first_pass_success_signal: {first_pass_success_rate:.2f} >= {self.FIRST_PASS_THRESHOLD}"
            )
        else:
            gate_blockers.append(
                f"first_pass_success_signal: {first_pass_success_rate:.2f} < {self.FIRST_PASS_THRESHOLD}"
            )

        # Retry discipline signal
        if retries_within_budget:
            gate_reasons.append("retry_discipline_signal: all retries within declared budget")
        else:
            gate_blockers.append(
                "retry_discipline_signal: one or more retries exceeded declared budget"
            )

        # Escalation rate signal
        if escalation_rate <= self.MAX_ESCALATION_RATE:
            gate_reasons.append(
                f"escalation_rate_signal: {escalation_rate:.2f} <= {self.MAX_ESCALATION_RATE}"
            )
        else:
            gate_blockers.append(
                f"escalation_rate_signal: {escalation_rate:.2f} > {self.MAX_ESCALATION_RATE}"
            )

        # Artifact completeness signal
        if artifact_completeness_signal:
            gate_reasons.append("artifact_completeness_signal: required artifact fields present")
        else:
            gate_blockers.append(
                "artifact_completeness_signal: required artifact fields missing"
            )

        gate_passed = len(gate_blockers) == 0

        signal_summary: Dict[str, Any] = {
            "first_pass_success_rate": first_pass_success_rate,
            "retries_within_budget": retries_within_budget,
            "escalation_rate": escalation_rate,
            "artifact_completeness_signal": artifact_completeness_signal,
        }
        if notes:
            signal_summary["notes"] = notes

        return LocalAutonomyGateResultV1(
            gate_passed=gate_passed,
            gate_reasons=gate_reasons,
            gate_blockers=gate_blockers,
            signal_summary=signal_summary,
        )
