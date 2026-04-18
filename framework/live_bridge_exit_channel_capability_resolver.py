from typing import Any
def resolve_exit_channel_capability(resolver_input):
    if not isinstance(resolver_input, dict): return {"exit_channel_capability_resolve_status": "invalid"}
    if "capability_id" not in resolver_input: return {"exit_channel_capability_resolve_status": "invalid"}
    return {"exit_channel_capability_resolve_status": "resolved", "capability_id": resolver_input.get("capability_id")}
