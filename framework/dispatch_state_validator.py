from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from framework.dispatch_state_tracker import track_dispatch_state_transition


@dataclass(frozen=True)
class ValidationError:
    job_id: str
    violation: str
    severity: str


@dataclass
class DispatchStateValidator:
    """Audits lifecycle transitions and enforces dispatch coherence."""

    state_history: dict[str, list[str]] = field(default_factory=dict)
    attempt_tracker: Any = field(default=None)

    def validate_transition(
        self,
        job_id: str,
        from_state: str,
        to_state: str,
    ) -> dict[str, Any]:
        """Validate a state transition."""
        result = track_dispatch_state_transition(job_id, from_state, to_state)

        if not result.get("state_valid", False):
            return {
                "job_id": job_id,
                "valid": False,
                "violation": "invalid_state_transition",
                "from_state": from_state,
                "to_state": to_state,
                "severity": "error",
            }

        if job_id not in self.state_history:
            self.state_history[job_id] = []
        self.state_history[job_id].append(to_state)

        return {
            "job_id": job_id,
            "valid": True,
            "from_state": from_state,
            "to_state": to_state,
        }

    def audit_state_coherence(
        self,
        jobs: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Audit state coherence across all jobs."""
        errors: list[tuple[str, str, str]] = []

        for job in jobs:
            job_id = job.get("job_id")
            lifecycle = job.get("lifecycle", "unknown")
            attempts_used = job.get("attempts_used", 0)

            if lifecycle == "failed" and attempts_used == 0:
                errors.append((
                    job_id,
                    "failed_with_zero_attempts",
                    "warning",
                ))

            if lifecycle == "completed" and job.get("status_reason"):
                if "error" in job.get("status_reason", "").lower():
                    errors.append((
                        job_id,
                        "completed_with_error_reason",
                        "warning",
                    ))

            if lifecycle not in [
                "accepted",
                "queued",
                "scheduled",
                "dispatching",
                "dispatched",
                "running",
                "retry_waiting",
                "completed",
                "failed",
                "escalated",
                "canceled",
            ]:
                errors.append((
                    job_id,
                    "unknown_lifecycle_state",
                    "error",
                ))

        return {
            "audit_timestamp": self._get_timestamp(),
            "jobs_audited": len(jobs),
            "errors_found": len(errors),
            "violations": [
                {"job_id": e[0], "violation": e[1], "severity": e[2]}
                for e in errors
            ],
        }

    def validate_attempt_consistency(
        self,
        job_id: str,
        expected_attempts: int,
    ) -> dict[str, Any]:
        """Validate attempt count matches tracker."""
        if not self.attempt_tracker:
            return {
                "job_id": job_id,
                "valid": True,
                "reason": "no_attempt_tracker",
            }

        actual_attempts = self.attempt_tracker.get_attempt_count(job_id)
        if actual_attempts != expected_attempts:
            return {
                "job_id": job_id,
                "valid": False,
                "violation": "attempt_count_mismatch",
                "expected": expected_attempts,
                "actual": actual_attempts,
                "severity": "error",
            }

        return {
            "job_id": job_id,
            "valid": True,
            "attempt_count": actual_attempts,
        }

    def get_state_history(self, job_id: str) -> list[str]:
        """Get recorded state transitions for job."""
        return self.state_history.get(job_id, [])

    def clear_state_history(self, job_id: str = None) -> None:
        """Clear state history for job or all jobs."""
        if job_id:
            if job_id in self.state_history:
                del self.state_history[job_id]
        else:
            self.state_history.clear()

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        from framework.compat import UTC
        return datetime.now(UTC).isoformat(timespec="seconds")
