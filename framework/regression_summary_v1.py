"""RegressionSummaryV1: summarize regression case outcomes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RegressionCaseV1:
    case_id: str
    task_class: str
    passed: bool
    failure_mode: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "task_class": self.task_class,
            "passed": self.passed,
            "failure_mode": self.failure_mode,
            "notes": self.notes,
        }


@dataclass
class RegressionSummaryV1:
    regression_cases_run: int
    regression_cases_passed: int
    pass_rate: float
    failure_modes: List[str]
    cases: List[RegressionCaseV1] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regression_cases_run": self.regression_cases_run,
            "regression_cases_passed": self.regression_cases_passed,
            "pass_rate": self.pass_rate,
            "failure_modes": self.failure_modes,
            "cases": [c.to_dict() for c in self.cases],
        }

    @classmethod
    def from_cases(cls, cases: List[RegressionCaseV1]) -> "RegressionSummaryV1":
        total = len(cases)
        passed = sum(1 for c in cases if c.passed)
        pass_rate = passed / total if total > 0 else 0.0
        failure_modes = [
            c.failure_mode for c in cases if not c.passed and c.failure_mode
        ]
        return cls(
            regression_cases_run=total,
            regression_cases_passed=passed,
            pass_rate=pass_rate,
            failure_modes=failure_modes,
            cases=cases,
        )
