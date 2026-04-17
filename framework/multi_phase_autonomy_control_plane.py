from typing import Any


def build_autonomy_control_plane(
    decision_validation: dict[str, Any],
    decision_rollup: dict[str, Any],
    event_bus: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(decision_validation, dict)
        or not isinstance(decision_rollup, dict)
        or not isinstance(event_bus, dict)
    ):
        return {
            "autonomy_cp_status": "invalid_input",
            "autonomy_phase": None,
            "component_count": 3,
        }

    validation_ok = decision_validation.get("decision_validation_status") == "valid"
    rollup_ok = decision_rollup.get("decision_rollup_status") == "rolled_up"
    all_complete = validation_ok and rollup_ok

    if all_complete and event_bus.get("message_count", -1) >= 0:
        return {
            "autonomy_cp_status": "operational",
            "autonomy_phase": decision_validation.get("validated_phase"),
            "component_count": 3,
        }

    if (validation_ok and not rollup_ok) or (rollup_ok and not validation_ok):
        return {
            "autonomy_cp_status": "degraded",
            "autonomy_phase": None,
            "component_count": 3,
        }

    return {
        "autonomy_cp_status": "offline",
        "autonomy_phase": None,
        "component_count": 3,
    }
