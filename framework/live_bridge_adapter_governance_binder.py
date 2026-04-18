from typing import Any

def bind_adapter_governance(scope: Any, fed_gov_cp: Any, binder_config: Any) -> dict[str, Any]:
    if not isinstance(scope, dict) or not isinstance(fed_gov_cp, dict):
        return {"adapter_governance_binding_status": "invalid_input"}
    s_ok = scope.get("adapter_scope_binding_status") == "bound"
    f_ok = fed_gov_cp.get("fed_gov_cp_status") == "operational"
    if not s_ok or not f_ok:
        return {"adapter_governance_binding_status": "invalid_input"}
    return {
        "adapter_governance_binding_status": "bound",
        "adapter_id": scope.get("adapter_id"),
        "fed_gov_operational": True,
    }
