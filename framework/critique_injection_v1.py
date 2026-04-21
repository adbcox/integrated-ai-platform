"""Critique injection surface for Phase 4 self-sufficiency uplift (P4-01)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from framework.failure_memory_v1 import FailureRecordV1


@dataclass
class CritiqueResultV1:
    task_class: str
    current_objective: str
    critique_points: List[str]
    retry_guidance: List[str]

    def to_dict(self) -> dict:
        return {
            "task_class": self.task_class,
            "current_objective": self.current_objective,
            "critique_points": self.critique_points,
            "retry_guidance": self.retry_guidance,
        }


_BASE_CRITIQUE: dict = {
    "bug_fix": [
        "Verify the fix targets the exact fault line, not a workaround.",
        "Confirm no adjacent logic is silently affected.",
    ],
    "narrow_feature": [
        "Confirm the feature scope is exactly as specified — no extras.",
        "Verify existing interfaces are unchanged.",
    ],
    "reporting_helper": [
        "All output fields must be serializable.",
        "No side effects inside the reporting logic.",
    ],
    "test_addition": [
        "Each test must be deterministic and offline-safe.",
        "Tests must not depend on execution order.",
    ],
}

_BASE_RETRY: dict = {
    "bug_fix": [
        "Re-read the failing trace before retrying.",
        "Narrow the patch scope if the first attempt touched multiple lines.",
    ],
    "narrow_feature": [
        "Re-read the task spec; confirm scope before second attempt.",
        "Start from a clean read of the target module.",
    ],
    "reporting_helper": [
        "Check all required fields against the spec before retrying.",
        "Run json.dumps() on the result dict to verify serializability.",
    ],
    "test_addition": [
        "Isolate the failing assertion; run the single test case before the suite.",
        "Remove any test-order dependencies.",
    ],
}

_GENERIC_CRITIQUE = ["Review the task objective carefully before retrying."]
_GENERIC_RETRY = ["Start from the task spec; do not carry over assumptions from the failed attempt."]


class CritiqueInjectionV1:
    def inject(
        self,
        task_class: str,
        prior_failures: List[FailureRecordV1],
        current_objective: str,
    ) -> CritiqueResultV1:
        critique_points: List[str] = list(_BASE_CRITIQUE.get(task_class, _GENERIC_CRITIQUE))
        retry_guidance: List[str] = list(_BASE_RETRY.get(task_class, _GENERIC_RETRY))

        for rec in prior_failures:
            if rec.failure_signature and rec.failure_signature not in critique_points:
                critique_points.append(f"Prior failure: {rec.failure_signature}")
            if rec.correction_hint and rec.correction_hint not in retry_guidance:
                retry_guidance.append(f"Hint from prior attempt: {rec.correction_hint}")

        return CritiqueResultV1(
            task_class=task_class,
            current_objective=current_objective,
            critique_points=critique_points,
            retry_guidance=retry_guidance,
        )
