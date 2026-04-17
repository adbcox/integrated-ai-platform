from typing import Any


def build_observability_control_plane(
    validation: dict[str, Any],
    metrics_rollup: dict[str, Any],
    event_bus: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(validation, dict)
        or not isinstance(metrics_rollup, dict)
        or not isinstance(event_bus, dict)
    ):
        return {
            "observability_cp_status": "invalid_input",
            "observability_phase": None,
            "component_count": 3,
        }

    validation_ok = validation.get("diagnostic_validation_status") == "valid"
    rollup_ok = metrics_rollup.get("metrics_rollup_status") == "rolled_up"
    all_complete = validation_ok and rollup_ok

    if all_complete and event_bus.get("message_count", -1) >= 0:
        return {
            "observability_cp_status": "operational",
            "observability_phase": validation.get("validated_phase"),
            "component_count": 3,
        }

    if (validation_ok and not rollup_ok) or (rollup_ok and not validation_ok):
        return {
            "observability_cp_status": "degraded",
            "observability_phase": None,
            "component_count": 3,
        }

    return {
        "observability_cp_status": "offline",
        "observability_phase": None,
        "component_count": 3,
    }
