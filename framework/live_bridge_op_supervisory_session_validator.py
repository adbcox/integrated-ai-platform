from typing import Any
def validate_supervisory_session(validation):
    if not isinstance(validation, dict): return {"op_supervisory_session_validation_status": "invalid"}
    if validation.get("op_supervisory_session_audit_status") != "audited": return {"op_supervisory_session_validation_status": "invalid"}
    return {"op_supervisory_session_validation_status": "valid", "audit_id": validation.get("audit_id")}
