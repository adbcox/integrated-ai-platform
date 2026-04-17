from typing import Any

def build_cycle_control_plane(cycle_validation: dict[str, Any], cycle_rollup: dict[str, Any], event_bus: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(cycle_validation, dict) or not isinstance(cycle_rollup, dict) or not isinstance(event_bus, dict):
        return {"cycle_cp_status": "invalid_input", "cycle_cp_env_id": None, "component_count": 0}
    cv_ok = cycle_validation.get("cycle_validation_status") == "valid"
    cr_ok = cycle_rollup.get("cycle_rollup_status") == "rolled_up"
    all_complete = cv_ok and cr_ok
    msg_count = event_bus.get("message_count", -1)
    if all_complete and isinstance(event_bus, dict) and msg_count >= 0:
        return {"cycle_cp_status": "operational", "cycle_cp_env_id": cycle_validation.get("validated_env_id"), "component_count": 3}
    if cv_ok != cr_ok:
        return {"cycle_cp_status": "degraded", "cycle_cp_env_id": None, "component_count": 0}
    return {"cycle_cp_status": "offline", "cycle_cp_env_id": None, "component_count": 0}
