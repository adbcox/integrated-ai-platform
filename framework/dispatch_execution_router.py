from typing import Any


def route_dispatch_execution(
    job: dict[str, Any],
    health_score: int,
    coherence_valid: bool,
    next_eligible_seconds: int,
    target_pool: list[str],
) -> dict[str, Any]:
    if not isinstance(job, dict) or not isinstance(target_pool, list):
        return {
            "route_valid": False,
            "dispatch_target": "",
            "route_reason": "invalid_input",
            "dispatch_now": False,
        }

    if next_eligible_seconds > 0:
        return {
            "route_valid": False,
            "dispatch_target": "",
            "route_reason": "backoff_not_elapsed",
            "dispatch_now": False,
        }

    if not coherence_valid:
        return {
            "route_valid": False,
            "dispatch_target": "",
            "route_reason": "coherence_invalid",
            "dispatch_now": False,
        }

    if health_score < 50:
        return {
            "route_valid": False,
            "dispatch_target": "",
            "route_reason": "poor_health_score",
            "dispatch_now": False,
        }

    target = target_pool[0] if target_pool else "local_executor"
    return {
        "route_valid": True,
        "dispatch_target": target,
        "route_reason": "eligible_for_dispatch",
        "dispatch_now": True,
    }
