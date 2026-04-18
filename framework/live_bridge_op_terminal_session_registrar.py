from typing import Any
def register_session(registration):
    if not isinstance(registration, dict): return {"op_session_registrar_status": "invalid"}
    if registration.get("op_session_validation_status") != "valid": return {"op_session_registrar_status": "invalid"}
    return {"op_session_registrar_status": "registered", "session_id": registration.get("session_id")}
