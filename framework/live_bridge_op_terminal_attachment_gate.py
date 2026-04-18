from typing import Any
def gate_attachment(attachment_descriptor, credential_validation):
    if not isinstance(attachment_descriptor, dict) or not isinstance(credential_validation, dict):
        return {"op_attachment_gate_status": "closed"}
    if "attachment_id" not in attachment_descriptor:
        return {"op_attachment_gate_status": "closed"}
    if credential_validation.get("op_credential_validation_status") != "valid":
        return {"op_attachment_gate_status": "closed"}
    return {"op_attachment_gate_status": "open", "attachment_id": attachment_descriptor.get("attachment_id")}
