from typing import Any

def catalog_adapter(attachment_gate: Any, identity: Any, catalog_state: Any) -> dict[str, Any]:
    if not isinstance(attachment_gate, dict) or not isinstance(identity, dict):
        return {"adapter_catalog_status": "uncataloged"}
    a_ok = attachment_gate.get("adapter_attachment_gate_status") == "open"
    i_ok = identity.get("adapter_identity_validation_status") == "valid"
    if not a_ok or not i_ok:
        return {"adapter_catalog_status": "uncataloged"}
    current_count = catalog_state.get("adapter_count", 0) if isinstance(catalog_state, dict) else 0
    return {
        "adapter_catalog_status": "cataloged",
        "adapter_id": identity.get("adapter_id"),
        "adapter_count": current_count + 1,
    }
