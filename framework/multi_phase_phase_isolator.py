from typing import Any


def isolate_phase_execution(
    coordinator: dict[str, Any],
    phase_id: str,
    isolation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(coordinator, dict)
        or not isinstance(phase_id, str)
        or not phase_id
        or not isinstance(isolation_config, dict)
    ):
        return {
            "isolation_status": "invalid_input",
            "isolated_phase": None,
            "isolation_level": None,
        }

    coordinator_status = coordinator.get("coordinator_status")
    coord_phase_id = coordinator.get("phase_id")

    if coordinator_status != "initialized":
        return {
            "isolation_status": "coordinator_not_ready",
            "isolated_phase": None,
            "isolation_level": None,
        }

    if coord_phase_id != phase_id:
        return {
            "isolation_status": "phase_mismatch",
            "isolated_phase": None,
            "isolation_level": None,
        }

    return {
        "isolation_status": "isolated",
        "isolated_phase": phase_id,
        "isolation_level": isolation_config.get("level", "standard"),
    }
