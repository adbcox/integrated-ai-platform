from typing import Any


def execute_phase_retry(
    recovery_plan: dict[str, Any],
    dispatch_result: dict[str, Any],
    attempt_count: int,
) -> dict[str, Any]:
    if (
        not isinstance(recovery_plan, dict)
        or not isinstance(dispatch_result, dict)
        or not isinstance(attempt_count, int)
        or attempt_count < 0
    ):
        return {
            "retry_status": "invalid_input",
            "attempt_number": attempt_count if isinstance(attempt_count, int) else 0,
            "recovery_phase": None,
        }

    if recovery_plan.get("recovery_status") != "planned":
        return {
            "retry_status": "no_plan",
            "attempt_number": attempt_count,
            "recovery_phase": None,
        }

    max_retries = int(recovery_plan.get("max_retries", 3))
    if attempt_count >= max_retries:
        return {
            "retry_status": "exhausted",
            "attempt_number": attempt_count,
            "recovery_phase": None,
        }

    return {
        "retry_status": "retried",
        "attempt_number": attempt_count + 1,
        "recovery_phase": recovery_plan.get("recovery_phase"),
    }
