from typing import Any


def apply_concurrency_limits(
    scheduler_result: dict[str, Any],
    limits: dict[str, Any],
    active_count: int,
) -> dict[str, Any]:
    if (
        not isinstance(scheduler_result, dict)
        or not isinstance(limits, dict)
        or not isinstance(active_count, int)
        or active_count < 0
    ):
        return {
            "limit_status": "invalid_input",
            "allowed_count": 0,
            "active_count": None,
        }

    max_concurrent = limits.get("max_concurrent", 1)
    if not isinstance(max_concurrent, int):
        max_concurrent = 1

    schedule_status = scheduler_result.get("schedule_status")

    if schedule_status != "scheduled":
        return {
            "limit_status": "not_scheduled",
            "allowed_count": 0,
            "active_count": active_count,
        }

    if active_count >= max_concurrent:
        return {
            "limit_status": "throttled",
            "allowed_count": 0,
            "active_count": active_count,
        }

    return {
        "limit_status": "allowed",
        "allowed_count": scheduler_result.get("scheduled_count", 0),
        "active_count": active_count,
    }
