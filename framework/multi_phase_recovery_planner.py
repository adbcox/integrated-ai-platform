from typing import Any


def plan_phase_recovery(
    failure: dict[str, Any],
    coordinator: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(failure, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(policy, dict)
    ):
        return {
            "recovery_status": "invalid_input",
            "recovery_phase": None,
            "strategy": None,
            "max_retries": 0,
        }

    if failure.get("failure_status") == "none":
        return {
            "recovery_status": "no_failure",
            "recovery_phase": None,
            "strategy": None,
            "max_retries": 0,
        }

    if (
        failure.get("failure_status") == "detected"
        and coordinator.get("coordinator_status") != "initialized"
    ):
        return {
            "recovery_status": "coordinator_not_ready",
            "recovery_phase": None,
            "strategy": None,
            "max_retries": 0,
        }

    if (
        failure.get("failure_status") == "detected"
        and coordinator.get("coordinator_status") == "initialized"
    ):
        return {
            "recovery_status": "planned",
            "recovery_phase": coordinator.get("phase_id"),
            "strategy": policy.get("strategy", "retry"),
            "max_retries": int(policy.get("max_retries", 3)),
        }

    return {
        "recovery_status": "invalid_input",
        "recovery_phase": None,
        "strategy": None,
        "max_retries": 0,
    }
