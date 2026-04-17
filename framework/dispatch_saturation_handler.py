from typing import Any


def evaluate_dispatch_saturation(
    queue_items: list[dict[str, Any]],
    queue_threshold: int,
    active_dispatches: int,
    active_limit: int,
) -> dict[str, Any]:
    if (
        not isinstance(queue_items, list)
        or queue_threshold < 0
        or active_dispatches < 0
        or active_limit < 0
    ):
        return {
            "saturation_valid": False,
            "backpressure_enabled": True,
            "available_dispatch_capacity": 0,
            "reason": "invalid_input",
        }

    queue_size = len(queue_items)
    saturated = queue_size > queue_threshold or active_dispatches >= active_limit
    available_capacity = max(0, active_limit - active_dispatches)

    reason = "within_limits"
    if queue_size > queue_threshold:
        reason = "queue_threshold_exceeded"
    elif active_dispatches >= active_limit:
        reason = "active_limit_reached"

    return {
        "saturation_valid": True,
        "backpressure_enabled": saturated,
        "available_dispatch_capacity": available_capacity,
        "reason": reason,
    }
