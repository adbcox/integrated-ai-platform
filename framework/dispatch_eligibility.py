from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from framework.compat import UTC
from framework.execution_dispatch_readiness_checker import check_dispatch_readiness


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    blocker: str | None
    next_check_at: str | None


@dataclass
class DispatchEligibilityChecker:
    """Evaluates if a job is eligible for dispatch now."""

    def check_eligibility(
        self,
        job: dict[str, Any],
        health_score: int,
        coherence_valid: bool,
        attempt_tracker: Any = None,
        queue_manager: Any = None,
    ) -> dict[str, Any]:
        """
        Check if job is eligible for dispatch.

        Validates: readiness, backoff, throttle.
        """
        job_id = job.get("job_id", "unknown")

        readiness = check_dispatch_readiness(job, health_score, coherence_valid)
        if not readiness.get("readiness_valid", False):
            return {
                "job_id": job_id,
                "eligible": False,
                "blocker": "readiness_check_failed",
                "blocking_factors": readiness.get("blocking_factors", []),
                "next_check_at": self._calculate_next_check(),
            }

        if attempt_tracker:
            if not attempt_tracker.is_eligible_now(job_id):
                next_eligible = attempt_tracker.get_next_eligible_time(job_id)
                return {
                    "job_id": job_id,
                    "eligible": False,
                    "blocker": "backoff_not_elapsed",
                    "next_eligible_at": next_eligible,
                    "next_check_at": next_eligible,
                }

        if queue_manager:
            job_class = job.get("task_class", "default")
            limit = queue_manager.get_throttle_limit(job_class)
            queue_size = queue_manager.get_queue_size()
            if queue_size >= limit:
                return {
                    "job_id": job_id,
                    "eligible": False,
                    "blocker": "throttle_limit_reached",
                    "queue_size": queue_size,
                    "throttle_limit": limit,
                    "next_check_at": self._calculate_next_check(delay_seconds=5),
                }

        return {
            "job_id": job_id,
            "eligible": True,
            "blocker": None,
            "readiness_score": readiness.get("readiness_score", 0),
            "next_check_at": None,
        }

    def _calculate_next_check(self, delay_seconds: int = 30) -> str:
        """Calculate when to check eligibility again."""
        from datetime import timedelta
        next_time = datetime.now(UTC) + timedelta(seconds=delay_seconds)
        return next_time.isoformat(timespec="seconds")
