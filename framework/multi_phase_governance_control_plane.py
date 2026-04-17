from typing import Any


def build_governance_control_plane(
    validation: dict[str, Any],
    rollup: dict[str, Any],
    event_bus: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(validation, dict)
        or not isinstance(rollup, dict)
        or not isinstance(event_bus, dict)
    ):
        return {
            "governance_cp_status": "invalid_input",
            "governance_phase": None,
            "component_count": 3,
        }

    validation_ok = validation.get("governance_validation_status") == "valid"
    rollup_ok = rollup.get("policy_rollup_status") == "rolled_up"
    all_complete = validation_ok and rollup_ok

    if all_complete and event_bus.get("message_count", -1) >= 0:
        return {
            "governance_cp_status": "operational",
            "governance_phase": validation.get("validated_phase"),
            "component_count": 3,
        }

    if (validation_ok and not rollup_ok) or (rollup_ok and not validation_ok):
        return {
            "governance_cp_status": "degraded",
            "governance_phase": None,
            "component_count": 3,
        }

    return {
        "governance_cp_status": "offline",
        "governance_phase": None,
        "component_count": 3,
    }
