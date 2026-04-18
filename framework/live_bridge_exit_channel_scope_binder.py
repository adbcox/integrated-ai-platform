from typing import Any
def bind_exit_channel_scope(binding):
    if not isinstance(binding, dict): return {"exit_channel_scope_bind_status": "invalid"}
    if binding.get("exit_channel_capability_resolve_status") != "resolved": return {"exit_channel_scope_bind_status": "invalid"}
    return {"exit_channel_scope_bind_status": "bound", "capability_id": binding.get("capability_id")}
