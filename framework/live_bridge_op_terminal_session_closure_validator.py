from typing import Any
def validate_session_closure(validation):
    if not isinstance(validation, dict): return {"op_session_closure_validation_status": "invalid"}
    if validation.get("op_session_close_status") != "closed": return {"op_session_closure_validation_status": "invalid"}
    return {"op_session_closure_validation_status": "valid", "session_id": validation.get("session_id")}
