from typing import Any


def collect_phase_metrics(
    coordinator: dict[str, Any],
    health: dict[str, Any],
    resource_tracker: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(coordinator, dict)
        or not isinstance(health, dict)
        or not isinstance(resource_tracker, dict)
    ):
        return {
            "metrics_status": "invalid_input",
            "collected_phase": None,
            "health_snapshot": None,
            "resource_count": 0,
        }

    coord_ok = coordinator.get("coordinator_status") == "initialized"
    if not coord_ok:
        return {
            "metrics_status": "coordinator_not_ready",
            "collected_phase": None,
            "health_snapshot": None,
            "resource_count": 0,
        }

    return {
        "metrics_status": "collected",
        "collected_phase": coordinator.get("phase_id"),
        "health_snapshot": health.get("health_status"),
        "resource_count": int(resource_tracker.get("phase_count", 0)),
    }
