from typing import Any
def resolve_command_scope(scope_input):
    if not isinstance(scope_input, dict): return {"op_scope_resolve_status": "invalid"}
    if "scope_id" not in scope_input: return {"op_scope_resolve_status": "invalid"}
    return {"op_scope_resolve_status": "resolved", "scope_id": scope_input.get("scope_id")}
