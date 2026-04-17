from typing import Any


def write_phase_snapshot(
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
            "snapshot_status": "invalid_input",
            "snapshot_phase": None,
            "resource_count": 0,
        }

    coordinator_status = coordinator.get("coordinator_status")
    health_status = health.get("health_status")
    phase_count = resource_tracker.get("phase_count", 0)

    if coordinator_status != "initialized":
        return {
            "snapshot_status": "coordinator_not_ready",
            "snapshot_phase": None,
            "resource_count": 0,
        }

    if health_status not in ("healthy", "degraded"):
        return {
            "snapshot_status": "invalid_input",
            "snapshot_phase": None,
            "resource_count": 0,
        }

    if phase_count == 0:
        return {
            "snapshot_status": "no_resources",
            "snapshot_phase": None,
            "resource_count": 0,
        }

    return {
        "snapshot_status": "written",
        "snapshot_phase": coordinator.get("phase_id"),
        "resource_count": phase_count,
    }
