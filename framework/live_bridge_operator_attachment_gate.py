from typing import Any

def gate_operator_attachment(scope_binding: dict, identity: dict, attachment_config: dict) -> dict:
    if not isinstance(scope_binding, dict) or not isinstance(identity, dict) or not isinstance(attachment_config, dict):
        return {"operator_attachment_gate_status": "invalid_input"}
    sb_ok = scope_binding.get("scope_binding_status") == "bound"
    i_ok = identity.get("operator_identity_status") == "valid"
    if not sb_ok:
        return {"operator_attachment_gate_status": "no_binding"}
    if not i_ok:
        return {"operator_attachment_gate_status": "no_identity"}
    return {
        "operator_attachment_gate_status": "open",
        "attached_operator_id": scope_binding.get("bound_operator_id"),
        "attachment_mode": attachment_config.get("mode", "interactive"),
    }
