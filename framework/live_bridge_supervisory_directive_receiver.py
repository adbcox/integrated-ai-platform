from typing import Any

def receive_directive(quorum_validation: dict, directive: dict, receiver_config: dict) -> dict:
    if not isinstance(quorum_validation, dict) or not isinstance(directive, dict) or not isinstance(receiver_config, dict):
        return {"directive_receipt_status": "invalid_input"}
    qv_ok = quorum_validation.get("quorum_validation_status") == "valid"
    d_valid = bool(directive.get("directive_id")) and directive.get("directive_kind") in ("intervene", "override", "veto", "rollback")
    if not qv_ok:
        return {"directive_receipt_status": "no_quorum"}
    if not d_valid:
        return {"directive_receipt_status": "invalid_directive"}
    return {
        "directive_receipt_status": "received",
        "received_directive_id": directive.get("directive_id"),
        "received_directive_kind": directive.get("directive_kind"),
        "received_quorum_id": quorum_validation.get("validated_quorum_id"),
    }
