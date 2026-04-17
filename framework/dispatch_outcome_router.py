from typing import Any


def route_dispatch_outcome(
    job_id: str,
    outcome_type: str,
    current_state: str,
) -> dict[str, Any]:
    if not job_id or not outcome_type:
        return {
            "outcome_valid": False,
            "next_handler": "",
            "next_state": "",
            "route_reason": "invalid_input",
        }

    if outcome_type == "success":
        target_state = "dispatched"
        handler = "complete_handler"
    elif outcome_type == "timeout":
        target_state = "scheduled"
        handler = "retry_handler"
    elif outcome_type == "failure":
        target_state = "scheduled"
        handler = "retry_handler"
    elif outcome_type == "cancelled":
        target_state = "dispatched"
        handler = "archive_handler"
    else:
        target_state = "scheduled"
        handler = "review_handler"

    return {
        "outcome_valid": True,
        "next_handler": handler,
        "next_state": target_state,
        "route_reason": outcome_type,
    }
