from typing import Any
def bind_command_scope(binding):
    if not isinstance(binding, dict): return {"op_scope_bind_status": "invalid"}
    if binding.get("op_scope_resolve_status") != "resolved": return {"op_scope_bind_status": "invalid"}
    return {"op_scope_bind_status": "bound", "scope_id": binding.get("scope_id")}
