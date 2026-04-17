from typing import Any

def validate_federation(fed_audit: dict[str, Any], cycle_cp: dict[str, Any], governance_cp: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(fed_audit, dict) or not isinstance(cycle_cp, dict) or not isinstance(governance_cp, dict):
        return {"fed_validation_status": "invalid_input"}
    a_ok = fed_audit.get("fed_audit_status") == "passed"
    c_ok = cycle_cp.get("cycle_cp_status") == "operational"
    g_ok = governance_cp.get("governance_cp_status") == "operational"
    if not a_ok:
        return {"fed_validation_status": "audit_failed"}
    return {"fed_validation_status": "valid"} if a_ok and c_ok and g_ok else {"fed_validation_status": "control_planes_offline"}

