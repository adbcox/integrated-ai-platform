from typing import Any
def validate_attachment(attachment_gate):
    if not isinstance(attachment_gate, dict):
        return {"op_attachment_validation_status": "invalid"}
    if attachment_gate.get("op_attachment_gate_status") != "open":
        return {"op_attachment_validation_status": "invalid"}
    return {"op_attachment_validation_status": "valid", "attachment_id": attachment_gate.get("attachment_id")}
