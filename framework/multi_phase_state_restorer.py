from typing import Any


def restore_phase_state(
    snapshot_read: dict[str, Any],
    coordinator: dict[str, Any],
    restoration_policy: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(snapshot_read, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(restoration_policy, dict)
    ):
        return {
            "restoration_status": "invalid_input",
            "restored_phase": None,
            "restored_resources": 0,
        }

    if snapshot_read.get("read_status") != "read":
        return {
            "restoration_status": "no_snapshot",
            "restored_phase": None,
            "restored_resources": 0,
        }

    if coordinator.get("coordinator_status") != "initialized":
        return {
            "restoration_status": "coordinator_not_ready",
            "restored_phase": None,
            "restored_resources": 0,
        }

    return {
        "restoration_status": "restored",
        "restored_phase": coordinator.get("phase_id"),
        "restored_resources": int(snapshot_read.get("resource_count", 0)),
    }
