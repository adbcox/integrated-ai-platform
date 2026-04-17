from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from framework.compat import UTC


@dataclass(frozen=True)
class AttemptRecord:
    job_id: str
    attempt: int
    timestamp: str
    reason: str
    next_eligible: str


@dataclass
class DispatchAttemptTracker:
    """Tracks retry attempts with exponential backoff enforcement."""

    attempts: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    backoff_base: int = 2
    backoff_cap: int = 3600

    def record_attempt(
        self,
        job_id: str,
        reason: str = "",
    ) -> dict[str, Any]:
        """Record a dispatch attempt for a job."""
        if job_id not in self.attempts:
            self.attempts[job_id] = []

        attempt_num = len(self.attempts[job_id]) + 1
        now = datetime.now(UTC)
        backoff_seconds = min(
            self.backoff_base ** (attempt_num - 1),
            self.backoff_cap,
        )
        next_eligible = (now + timedelta(seconds=backoff_seconds)).isoformat(
            timespec="seconds"
        )

        self.attempts[job_id].append({
            "attempt": attempt_num,
            "timestamp": now.isoformat(timespec="seconds"),
            "reason": reason,
            "next_eligible": next_eligible,
        })

        return {
            "job_id": job_id,
            "attempt": attempt_num,
            "recorded": True,
            "backoff_seconds": backoff_seconds,
            "next_eligible": next_eligible,
        }

    def get_attempt_count(self, job_id: str) -> int:
        """Return number of attempts for job."""
        return len(self.attempts.get(job_id, []))

    def is_eligible_now(self, job_id: str) -> bool:
        """Check if job can be retried (backoff elapsed)."""
        if job_id not in self.attempts or not self.attempts[job_id]:
            return True

        last_attempt = self.attempts[job_id][-1]
        next_eligible = datetime.fromisoformat(last_attempt["next_eligible"])
        now = datetime.now(UTC)
        return now >= next_eligible

    def get_next_eligible_time(self, job_id: str) -> str | None:
        """Return when job becomes eligible for retry."""
        if job_id not in self.attempts or not self.attempts[job_id]:
            return None
        return self.attempts[job_id][-1].get("next_eligible")

    def get_last_failure_reason(self, job_id: str) -> str | None:
        """Return reason of last attempt."""
        if job_id not in self.attempts or not self.attempts[job_id]:
            return None
        return self.attempts[job_id][-1].get("reason")

    def get_attempt_history(self, job_id: str) -> list[dict[str, Any]]:
        """Return all attempt records for job."""
        return self.attempts.get(job_id, [])

    def clear_attempts(self, job_id: str) -> dict[str, Any]:
        """Clear attempt history for job (on success)."""
        if job_id in self.attempts:
            count = len(self.attempts[job_id])
            del self.attempts[job_id]
            return {"job_id": job_id, "cleared": True, "attempts_removed": count}
        return {"job_id": job_id, "cleared": False, "attempts_removed": 0}
