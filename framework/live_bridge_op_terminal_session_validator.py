from typing import Any
def validate_session(validation):
    if not isinstance(validation, dict): return {"op_session_validation_status": "invalid"}
    if validation.get("op_session_open_status") != "opened": return {"op_session_validation_status": "invalid"}
    return {"op_session_validation_status": "valid", "session_id": validation.get("session_id")}
