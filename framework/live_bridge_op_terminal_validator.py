from typing import Any
def validate_terminal(validation):
    if not isinstance(validation, dict): return {"op_terminal_validation_status": "invalid"}
    if validation.get("op_terminal_audit_status") != "audited": return {"op_terminal_validation_status": "invalid"}
    return {"op_terminal_validation_status": "valid", "audit_id": validation.get("audit_id")}
