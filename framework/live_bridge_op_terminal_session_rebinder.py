from typing import Any
def rebind_session(rebinding):
    if not isinstance(rebinding, dict): return {"op_session_rebind_status": "invalid"}
    if rebinding.get("op_session_index_status") != "indexed": return {"op_session_rebind_status": "invalid"}
    return {"op_session_rebind_status": "rebound", "session_id": rebinding.get("session_id")}
