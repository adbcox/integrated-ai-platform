from typing import Any

def validate_cycle(cycle_audit: dict[str, Any], bridge_cp: dict[str, Any], governance_cp: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(cycle_audit, dict) or not isinstance(bridge_cp, dict) or not isinstance(governance_cp, dict):
        return {"cycle_validation_status": "invalid_input", "validated_env_id": None, "cycle_complete": False}
    ca_ok = cycle_audit.get("cycle_audit_status") == "passed"
    cp_op = bridge_cp.get("bridge_cp_status") == "operational"
    g_op = governance_cp.get("governance_cp_status") == "operational"
    all_ok = ca_ok and cp_op and g_op
    if all_ok:
        return {"cycle_validation_status": "valid", "validated_env_id": bridge_cp.get("bridge_cp_env_id"), "cycle_complete": True}
    if ca_ok and (cp_op != g_op):
        return {"cycle_validation_status": "partial", "validated_env_id": None, "cycle_complete": False}
    if cycle_audit.get("cycle_audit_status") == "failed":
        return {"cycle_validation_status": "failed", "validated_env_id": None, "cycle_complete": False}
    return {"cycle_validation_status": "invalid_input", "validated_env_id": None, "cycle_complete": False}
