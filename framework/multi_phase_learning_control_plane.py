from typing import Any


def build_learning_control_plane(
    validation: dict[str, Any],
    knowledge_rollup: dict[str, Any],
    event_bus: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(validation, dict)
        or not isinstance(knowledge_rollup, dict)
        or not isinstance(event_bus, dict)
    ):
        return {
            "learning_cp_status": "invalid_input",
            "learning_phase": None,
            "component_count": 3,
        }

    validation_ok = validation.get("learning_validation_status") == "valid"
    rollup_ok = knowledge_rollup.get("knowledge_rollup_status") == "rolled_up"
    all_complete = validation_ok and rollup_ok

    if all_complete and event_bus.get("message_count", -1) >= 0:
        return {
            "learning_cp_status": "operational",
            "learning_phase": validation.get("validated_phase"),
            "component_count": 3,
        }

    if (validation_ok and not rollup_ok) or (rollup_ok and not validation_ok):
        return {
            "learning_cp_status": "degraded",
            "learning_phase": None,
            "component_count": 3,
        }

    return {
        "learning_cp_status": "offline",
        "learning_phase": None,
        "component_count": 3,
    }
