from typing import Any


def evaluate_circuit_state(
    health_status: dict[str, Any],
    failure_count: int,
    failure_threshold: int,
    recovery_allowed: bool,
) -> dict[str, Any]:
    if (
        not isinstance(health_status, dict)
        or not isinstance(failure_count, int)
        or not isinstance(failure_threshold, int)
        or not isinstance(recovery_allowed, bool)
    ):
        return {
            "circuit_status": "invalid_input",
            "circuit_state": None,
            "open": False,
        }

    if failure_threshold <= 0:
        return {
            "circuit_status": "invalid_input",
            "circuit_state": None,
            "open": False,
        }

    health_ok = health_status.get("health_state") == "healthy"

    if not health_ok and failure_count >= failure_threshold:
        return {
            "circuit_status": "evaluated",
            "circuit_state": "open",
            "open": True,
        }

    if not health_ok and failure_count >= (failure_threshold // 2):
        return {
            "circuit_status": "evaluated",
            "circuit_state": "half_open",
            "open": False,
        }

    if recovery_allowed and not health_ok:
        return {
            "circuit_status": "evaluated",
            "circuit_state": "half_open",
            "open": False,
        }

    return {
        "circuit_status": "evaluated",
        "circuit_state": "closed",
        "open": False,
    }
