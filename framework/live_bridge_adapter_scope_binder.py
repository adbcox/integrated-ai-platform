from typing import Any

def bind_adapter_scope(capability: Any, fed_cp: Any, scope_config: Any) -> dict[str, Any]:
    if not isinstance(capability, dict) or not isinstance(fed_cp, dict):
        return {"adapter_scope_binding_status": "invalid_input"}
    c_ok = capability.get("adapter_capability_resolution_status") == "resolved"
    f_ok = fed_cp.get("fed_cp_status") == "operational"
    if not c_ok or not f_ok:
        return {"adapter_scope_binding_status": "invalid_input"}
    return {
        "adapter_scope_binding_status": "bound",
        "adapter_id": capability.get("adapter_id"),
        "fed_cp_operational": True,
    }
