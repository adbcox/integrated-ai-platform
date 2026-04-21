"""LACE1-P4-RETRY-REPAIR-POLICY-SEAM-1: typed repair-policy decision gate."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.bounded_retry_controller import BoundedRetryController
from framework.retry_policy_schema import RetryPolicy

assert callable(BoundedRetryController), "INTERFACE MISMATCH: BoundedRetryController not callable"
assert "max_attempts" in RetryPolicy.__dataclass_fields__, "INTERFACE MISMATCH: RetryPolicy.max_attempts"
assert "retry_on_validation_failure" in RetryPolicy.__dataclass_fields__, "INTERFACE MISMATCH: RetryPolicy.retry_on_validation_failure"
assert "retry_on_execution_failure" in RetryPolicy.__dataclass_fields__, "INTERFACE MISMATCH: RetryPolicy.retry_on_execution_failure"

_VALID_ACTIONS = {"retry", "escalate_critique", "hard_stop"}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class FailureRecord:
    failure_id: str
    failure_kind: str    # "validation_failure"|"execution_failure"|"timeout"|"unknown"
    attempt_number: int
    error_summary: str


@dataclass(frozen=True)
class RepairDecision:
    failure_id: str
    action: str          # "retry"|"escalate_critique"|"hard_stop"
    reason: str
    attempt_number: int
    max_attempts_reached: bool
    decided_at: str


class RepairPolicyGate:
    """Typed repair-policy decision surface. Does not modify existing retry infrastructure."""

    def __init__(self, policy: RetryPolicy) -> None:
        self._policy = policy

    def decide(self, failure: FailureRecord) -> RepairDecision:
        policy = self._policy

        if failure.attempt_number >= policy.max_attempts:
            return RepairDecision(
                failure_id=failure.failure_id,
                action="hard_stop",
                reason=f"max_attempts={policy.max_attempts} reached at attempt {failure.attempt_number}",
                attempt_number=failure.attempt_number,
                max_attempts_reached=True,
                decided_at=_iso_now(),
            )

        if failure.failure_kind == "validation_failure":
            if policy.retry_on_validation_failure:
                action = "retry"
                reason = "validation_failure with retry_on_validation_failure=True"
            else:
                action = "escalate_critique"
                reason = "validation_failure with retry_on_validation_failure=False"
        elif failure.failure_kind == "execution_failure":
            if policy.retry_on_execution_failure:
                action = "retry"
                reason = "execution_failure with retry_on_execution_failure=True"
            else:
                action = "hard_stop"
                reason = "execution_failure with retry_on_execution_failure=False"
        else:
            action = "hard_stop"
            reason = f"unhandled failure_kind={failure.failure_kind!r}"

        assert action in _VALID_ACTIONS, f"Internal error: action {action!r} not in valid set"

        return RepairDecision(
            failure_id=failure.failure_id,
            action=action,
            reason=reason,
            attempt_number=failure.attempt_number,
            max_attempts_reached=False,
            decided_at=_iso_now(),
        )


__all__ = ["FailureRecord", "RepairDecision", "RepairPolicyGate"]
