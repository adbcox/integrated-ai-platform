from typing import Any

def catalog_operator(attachment_gate: dict, identity: dict, catalog_state: dict) -> dict:
    if not isinstance(attachment_gate, dict) or not isinstance(identity, dict) or not isinstance(catalog_state, dict):
        return {"operator_catalog_status": "invalid_input"}
    ag_ok = attachment_gate.get("operator_attachment_gate_status") == "open"
    i_ok = identity.get("operator_identity_status") == "valid"
    if not ag_ok:
        return {"operator_catalog_status": "not_attached"}
    return {
        "operator_catalog_status": "cataloged",
        "catalog_operator_id": attachment_gate.get("attached_operator_id"),
        "catalog_entry": int(catalog_state.get("count", 0)) + 1,
        "catalog_kind": identity.get("validated_operator_kind"),
    }
