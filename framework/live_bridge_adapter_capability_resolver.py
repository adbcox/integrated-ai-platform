from typing import Any

def resolve_adapter_capability(identity: Any, fed_gov_cp: Any, capability_config: Any) -> dict[str, Any]:
    if not isinstance(identity, dict) or not isinstance(fed_gov_cp, dict):
        return {"adapter_capability_resolution_status": "invalid_input"}
    i_ok = identity.get("adapter_identity_validation_status") == "valid"
    f_ok = fed_gov_cp.get("fed_gov_cp_status") == "operational"
    if not i_ok or not f_ok:
        return {"adapter_capability_resolution_status": "invalid_input"}
    return {
        "adapter_capability_resolution_status": "resolved",
        "adapter_id": identity.get("adapter_id"),
        "fed_gov_operational": True,
    }
