from typing import Any


def restore_from_checkpoint(
    bridge: dict[str, Any],
    coordinator: dict[str, Any],
    restore_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(bridge, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(restore_config, dict)
    ):
        return {
            "checkpoint_restore_status": "invalid_input",
            "restored_phase": None,
            "approved_releases": 0,
        }

    if bridge.get("bridge_status") != "bridged":
        return {
            "checkpoint_restore_status": "bridge_incomplete",
            "restored_phase": None,
            "approved_releases": 0,
        }

    if coordinator.get("coordinator_status") != "initialized":
        return {
            "checkpoint_restore_status": "coordinator_not_ready",
            "restored_phase": None,
            "approved_releases": 0,
        }

    return {
        "checkpoint_restore_status": "restored",
        "restored_phase": coordinator.get("phase_id"),
        "approved_releases": int(bridge.get("approved_releases", 0)),
    }
