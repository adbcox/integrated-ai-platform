from typing import Any


def apply_backpressure(
    health_status: dict[str, Any],
    active_count: int,
    max_active: int,
    backpressure_enabled: bool,
) -> dict[str, Any]:
    if (
        not isinstance(health_status, dict)
        or not isinstance(active_count, int)
        or not isinstance(max_active, int)
        or not isinstance(backpressure_enabled, bool)
    ):
        return {
            "backpressure_status": "invalid_input",
            "pressure_applied": False,
            "throttle_factor": 0,
        }

    if max_active <= 0:
        return {
            "backpressure_status": "invalid_input",
            "pressure_applied": False,
            "throttle_factor": 0,
        }

    if not backpressure_enabled:
        return {
            "backpressure_status": "disabled",
            "pressure_applied": False,
            "throttle_factor": 0,
        }

    health_ok = health_status.get("health_state") == "healthy"
    if not health_ok:
        return {
            "backpressure_status": "applied",
            "pressure_applied": True,
            "throttle_factor": 0.5,
        }

    utilization = active_count / max_active if max_active > 0 else 0
    if utilization >= 0.9:
        return {
            "backpressure_status": "applied",
            "pressure_applied": True,
            "throttle_factor": 0.3,
        }

    if utilization >= 0.7:
        return {
            "backpressure_status": "partial",
            "pressure_applied": True,
            "throttle_factor": 0.1,
        }

    return {
        "backpressure_status": "none",
        "pressure_applied": False,
        "throttle_factor": 0,
    }
