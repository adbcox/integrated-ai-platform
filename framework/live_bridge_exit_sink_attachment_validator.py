from typing import Any
def validate_exit_sink_attachment(validation):
    if not isinstance(validation, dict): return {"exit_sink_attachment_validation_status": "invalid"}
    if validation.get("exit_sink_attachment_gate_status") != "open": return {"exit_sink_attachment_validation_status": "invalid"}
    return {"exit_sink_attachment_validation_status": "valid", "attachment_id": validation.get("attachment_id")}
