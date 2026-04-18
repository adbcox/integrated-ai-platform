from typing import Any
def close_session(closer_input):
    if not isinstance(closer_input, dict): return {"op_session_close_status": "invalid"}
    if "session_id" not in closer_input: return {"op_session_close_status": "invalid"}
    return {"op_session_close_status": "closed", "session_id": closer_input.get("session_id")}
