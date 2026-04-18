from typing import Any

def validate_adapter_layer(adapter_audit: Any, fed_gov_cp: Any, governance_cp: Any) -> dict[str, Any]:
    if not isinstance(adapter_audit, dict) or not isinstance(fed_gov_cp, dict) or not isinstance(governance_cp, dict):
        return {"adapter_validation_status": "failed"}
    a_ok = adapter_audit.get("adapter_layer_audit_status") == "passed"
    f_ok = fed_gov_cp.get("fed_gov_cp_status") == "operational"
    g_ok = governance_cp.get("governance_cp_status") == "operational"
    if not a_ok or not f_ok or not g_ok:
        return {"adapter_validation_status": "failed"}
    return {
        "adapter_validation_status": "valid",
        "checkpoint_count": 3,
    }
