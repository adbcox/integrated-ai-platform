from typing import Any
def index_session(indexing):
    if not isinstance(indexing, dict): return {"op_session_index_status": "invalid"}
    if indexing.get("op_session_registrar_status") != "registered": return {"op_session_index_status": "invalid"}
    return {"op_session_index_status": "indexed", "session_id": indexing.get("session_id")}
