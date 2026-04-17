from typing import Any

def validate_fed_governance(fed_gov_audit: dict, fed_cp: dict, governance_cp: dict) -> dict:
    if not isinstance(fed_gov_audit, dict) or not isinstance(fed_cp, dict) or not isinstance(governance_cp, dict):
        return {"fed_gov_validation_status": "invalid_input"}
    fa_ok = fed_gov_audit.get("fed_gov_audit_status") == "passed"
    cp_op = fed_cp.get("fed_cp_status") == "operational"
    g_op = governance_cp.get("governance_cp_status") == "operational"
    all_ok = fa_ok and cp_op and g_op
    if all_ok:
        return {
            "fed_gov_validation_status": "valid",
            "validated_fed_gov_env_id": fed_cp.get("fed_cp_env_id"),
            "fed_gov_complete": True,
        }
    if fa_ok and (cp_op == g_op):
        return {"fed_gov_validation_status": "partial", "fed_gov_complete": False}
    return {"fed_gov_validation_status": "failed", "fed_gov_complete": False}
