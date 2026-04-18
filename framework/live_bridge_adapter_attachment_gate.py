from typing import Any

def gate_adapter_attachment(governance_binding: Any, identity: Any, attachment_config: Any) -> dict[str, Any]:
    if not isinstance(governance_binding, dict) or not isinstance(identity, dict):
        return {"adapter_attachment_gate_status": "closed"}
    g_ok = governance_binding.get("adapter_governance_binding_status") == "bound"
    i_ok = identity.get("adapter_identity_validation_status") == "valid"
    if not g_ok or not i_ok:
        return {"adapter_attachment_gate_status": "closed"}
    return {
        "adapter_attachment_gate_status": "open",
        "adapter_id": identity.get("adapter_id"),
    }
