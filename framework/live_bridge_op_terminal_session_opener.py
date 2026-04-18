from typing import Any
def open_session(session_input):
    if not isinstance(session_input, dict): return {"op_session_open_status": "invalid"}
    if "session_id" not in session_input: return {"op_session_open_status": "invalid"}
    return {"op_session_open_status": "opened", "session_id": session_input.get("session_id")}
