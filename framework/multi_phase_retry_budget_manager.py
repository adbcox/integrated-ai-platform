from typing import Any


def manage_retry_budget(
    current_budget: int,
    attempt_number: int,
    max_retries: int,
) -> dict[str, Any]:
    if (
        not isinstance(current_budget, int)
        or not isinstance(attempt_number, int)
        or not isinstance(max_retries, int)
    ):
        return {
            "budget_status": "invalid_input",
            "budget_remaining": None,
            "budget_depleted": False,
        }

    if max_retries <= 0:
        return {
            "budget_status": "invalid_input",
            "budget_remaining": None,
            "budget_depleted": False,
        }

    if current_budget <= 0:
        return {
            "budget_status": "budget_depleted",
            "budget_remaining": 0,
            "budget_depleted": True,
        }

    if attempt_number > max_retries:
        remaining = max(0, current_budget - (attempt_number - 1))
        return {
            "budget_status": "budget_exceeded",
            "budget_remaining": remaining,
            "budget_depleted": True,
        }

    remaining = max(0, current_budget - attempt_number)
    status = "available" if remaining > 0 else "last_attempt"

    return {
        "budget_status": status,
        "budget_remaining": remaining,
        "budget_depleted": remaining <= 0,
    }
