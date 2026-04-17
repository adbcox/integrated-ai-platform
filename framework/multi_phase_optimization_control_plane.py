from typing import Any


def build_optimization_control_plane(
    validation: dict[str, Any],
    optimization_rollup: dict[str, Any],
    event_bus: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(validation, dict)
        or not isinstance(optimization_rollup, dict)
        or not isinstance(event_bus, dict)
    ):
        return {
            "optimization_cp_status": "invalid_input",
            "optimization_phase": None,
            "component_count": 3,
        }

    validation_ok = validation.get("adaptation_validation_status") == "valid"
    rollup_ok = optimization_rollup.get("optimization_rollup_status") == "rolled_up"
    all_complete = validation_ok and rollup_ok

    if all_complete and event_bus.get("message_count", -1) >= 0:
        return {
            "optimization_cp_status": "operational",
            "optimization_phase": validation.get("validated_phase"),
            "component_count": 3,
        }

    if (validation_ok and not rollup_ok) or (rollup_ok and not validation_ok):
        return {
            "optimization_cp_status": "degraded",
            "optimization_phase": None,
            "component_count": 3,
        }

    return {
        "optimization_cp_status": "offline",
        "optimization_phase": None,
        "component_count": 3,
    }
