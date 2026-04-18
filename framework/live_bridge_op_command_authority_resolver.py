from typing import Any
def resolve_command_authority(authority_input):
    if not isinstance(authority_input, dict): return {"op_authority_resolve_status": "invalid"}
    auth_level = authority_input.get("authority_level")
    if auth_level not in ("admin", "operator", "guest"): return {"op_authority_resolve_status": "invalid"}
    return {"op_authority_resolve_status": "resolved", "authority_level": auth_level}
