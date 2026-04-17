from typing import Any

def build_federation_control_plane(fed_validation: dict[str, Any], fed_session_rollup: dict[str, Any], event_bus: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fed_validation, dict) or not isinstance(fed_session_rollup, dict) or not isinstance(event_bus, dict):
        return {"fed_cp_status": "invalid_input"}
    v_ok = fed_validation.get("fed_validation_status") == "valid"
    s_ok = fed_session_rollup.get("fed_session_rollup_status") == "rolled_up"
    e_ok = event_bus.get("message_count", 0) >= 0
    all_complete = v_ok and s_ok and e_ok
    if not all_complete:
        return {"fed_cp_status": "prerequisites_failed"}
    return {"fed_cp_status": "operational"}

