from typing import Any


def build_recovery_control_plane(
    validator: dict[str, Any],
    rollup: dict[str, Any],
    event_bus: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(validator, dict)
        or not isinstance(rollup, dict)
        or not isinstance(event_bus, dict)
    ):
        return {
            "recovery_cp_status": "invalid_input",
            "recovery_phase": None,
            "component_count": 3,
        }

    validator_ok = validator.get("validation_status") == "valid"
    rollup_ok = rollup.get("rollup_status") == "rolled_up"
    all_complete = validator_ok and rollup_ok

    if all_complete and event_bus.get("message_count", -1) >= 0:
        return {
            "recovery_cp_status": "operational",
            "recovery_phase": validator.get("validated_phase"),
            "component_count": 3,
        }

    if (validator_ok and not rollup_ok) or (rollup_ok and not validator_ok):
        return {
            "recovery_cp_status": "degraded",
            "recovery_phase": None,
            "component_count": 3,
        }

    return {
        "recovery_cp_status": "offline",
        "recovery_phase": None,
        "component_count": 3,
    }
