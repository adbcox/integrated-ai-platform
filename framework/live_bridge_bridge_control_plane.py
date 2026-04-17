from typing import Any
def build_bridge_control_plane(bridge_validation: dict[str, Any], session_rollup: dict[str, Any], event_bus: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bridge_validation, dict) or not isinstance(session_rollup, dict) or not isinstance(event_bus, dict):
        return {"bridge_cp_status": "offline", "bridge_cp_env_id": None, "component_count": 0}
    bv_ok = bridge_validation.get("bridge_validation_status") == "valid"
    sr_ok = session_rollup.get("session_rollup_status") == "rolled_up"
    all_complete = bv_ok and sr_ok
    if all_complete and event_bus.get("message_count", -1) >= 0:
        return {"bridge_cp_status": "operational", "bridge_cp_env_id": bridge_validation.get("validated_bridge_phase"), "component_count": 3}
    if bv_ok != sr_ok:
        return {"bridge_cp_status": "degraded", "bridge_cp_env_id": None, "component_count": 0}
    return {"bridge_cp_status": "offline", "bridge_cp_env_id": None, "component_count": 0}
