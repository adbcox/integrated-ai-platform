from typing import Any


def build_resilience_control_plane(
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
            "resilience_cp_status": "invalid_input",
            "resilience_phase": None,
            "component_count": 3,
        }

    validator_ok = validator.get("resilience_validation_status") == "valid"
    rollup_ok = rollup.get("load_balancing_rollup_status") == "rolled_up"
    all_complete = validator_ok and rollup_ok

    if all_complete and event_bus.get("message_count", -1) >= 0:
        return {
            "resilience_cp_status": "operational",
            "resilience_phase": validator.get("all_constraints_met"),
            "component_count": 3,
        }

    if (validator_ok and not rollup_ok) or (rollup_ok and not validator_ok):
        return {
            "resilience_cp_status": "degraded",
            "resilience_phase": None,
            "component_count": 3,
        }

    return {
        "resilience_cp_status": "offline",
        "resilience_phase": None,
        "component_count": 3,
    }
