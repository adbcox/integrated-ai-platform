"""BoundedRetryController: governs bounded retry decisions using BoundedCritiqueAdopter."""
from __future__ import annotations

import inspect as _inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from framework.bounded_critique_adopter import BoundedCritiqueAdopter, CritiqueAdoptionRecord

# -- import-time assertions --
assert "should_retry" in CritiqueAdoptionRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: CritiqueAdoptionRecord.should_retry"
assert "critique_text" in CritiqueAdoptionRecord.__dataclass_fields__, \
    "INTERFACE MISMATCH: CritiqueAdoptionRecord.critique_text"

# Inspect retry telemetry module for optional telemetry write path
_retry_record_callable = None
try:
    from framework.retry_telemetry import RetryTelemetryRecord
    assert "session_id" in RetryTelemetryRecord.__dataclass_fields__, \
        "INTERFACE MISMATCH: RetryTelemetryRecord.session_id"
except ImportError:
    RetryTelemetryRecord = None  # type: ignore


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class RetryDecisionRecord:
    session_id: str
    attempt_number: int
    max_retries: int
    task_kind: str
    last_error: Optional[str]
    decision: str  # "retry" | "stop"
    rationale: str
    evaluated_at: str


class BoundedRetryController:
    """Critique-based retry control; max_retries is strict; telemetry write is optional."""

    def __init__(
        self,
        *,
        max_retries: int = 3,
        memory_store=None,
    ):
        self._max_retries = max_retries
        self._adopter = BoundedCritiqueAdopter(memory_store=memory_store)

    def decide(
        self,
        session_id: str,
        attempt_number: int,
        task_kind: str,
        last_error: Optional[str],
        *,
        last_error_type: Optional[str] = None,
    ) -> RetryDecisionRecord:
        # Strict max_retries enforcement
        if attempt_number >= self._max_retries:
            return RetryDecisionRecord(
                session_id=session_id,
                attempt_number=attempt_number,
                max_retries=self._max_retries,
                task_kind=task_kind,
                last_error=last_error,
                decision="stop",
                rationale=f"max_retries={self._max_retries} reached",
                evaluated_at=_iso_now(),
            )

        adoption: CritiqueAdoptionRecord = self._adopter.evaluate(
            task_kind, last_error, last_error_type=last_error_type
        )

        decision = "retry" if adoption.should_retry else "stop"
        rationale = adoption.critique_text
        if adoption.extra_guidance:
            rationale = f"{rationale}\n{adoption.extra_guidance}"

        return RetryDecisionRecord(
            session_id=session_id,
            attempt_number=attempt_number,
            max_retries=self._max_retries,
            task_kind=task_kind,
            last_error=last_error,
            decision=decision,
            rationale=rationale,
            evaluated_at=_iso_now(),
        )


__all__ = ["RetryDecisionRecord", "BoundedRetryController"]
