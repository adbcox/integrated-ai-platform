from typing import Any
def validate_bridge(bridge_audit: dict[str, Any], boundary_guard: dict[str, Any], governance_cp: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bridge_audit, dict) or not isinstance(boundary_guard, dict) or not isinstance(governance_cp, dict):
        return {"bridge_validation_status": "invalid_input", "validated_bridge_phase": None, "bridge_complete": False}
    ba_ok = bridge_audit.get("bridge_audit_status") == "passed"
    bg_ok = boundary_guard.get("boundary_guard_status") == "armed"
    g_ok = governance_cp.get("governance_cp_status") == "operational"
    if ba_ok and bg_ok and g_ok:
        return {"bridge_validation_status": "valid", "validated_bridge_phase": boundary_guard.get("guard_env_id"), "bridge_complete": True}
    return {"bridge_validation_status": "partial" if (ba_ok or bg_ok or g_ok) else "failed", "validated_bridge_phase": None, "bridge_complete": False}
