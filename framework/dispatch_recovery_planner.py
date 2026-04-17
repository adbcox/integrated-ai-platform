from typing import Any

from framework.dispatch_fallback_scheduler import schedule_dispatch_fallback


def plan_dispatch_recovery(
    job_id: str,
    attempt: int,
    failure_reason: str,
    max_attempts: int,
) -> dict[str, Any]:
    if not job_id or attempt < 0 or max_attempts < 0:
        return {
            "plan_valid": False,
            "action": "invalid",
            "schedule_after_seconds": 0,
            "escalate": False,
        }

    fallback = schedule_dispatch_fallback(
        job_id,
        attempt,
        failure_reason,
        "2026-04-17T00:00:00Z",
        max_attempts,
    )

    return {
        "plan_valid": fallback.get("schedule_valid", False),
        "action": fallback.get("action", "invalid"),
        "schedule_after_seconds": fallback.get("schedule_after_seconds", 0),
        "escalate": fallback.get("escalate", False),
    }


def summarize_recovery_actions(
    plans: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(plans, list):
        return {"summary_valid": False, "retry_count": 0, "escalate_count": 0}

    valid = [p for p in plans if isinstance(p, dict)]
    retry_count = len([p for p in valid if p.get("action") == "retry"])
    escalate_count = len([p for p in valid if p.get("action") == "escalate"])

    return {
        "summary_valid": True,
        "retry_count": retry_count,
        "escalate_count": escalate_count,
    }
