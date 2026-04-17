from typing import Any


def schedule_dispatch_fallback(
    job_id: str,
    attempt: int,
    failure_reason: str,
    timestamp: str,
    max_attempts: int,
) -> dict[str, Any]:
    if not job_id or attempt < 0 or max_attempts < 0:
        return {
            "schedule_valid": False,
            "action": "invalid",
            "schedule_after_seconds": 0,
            "escalate": False,
        }

    if attempt >= max_attempts:
        return {
            "schedule_valid": True,
            "action": "escalate",
            "schedule_after_seconds": 0,
            "escalate": True,
        }

    backoff_seconds = min(2 ** attempt, 3600)
    return {
        "schedule_valid": True,
        "action": "retry",
        "schedule_after_seconds": backoff_seconds,
        "escalate": False,
    }
