from typing import Any
def build_audit_trail(builder_input):
    if not isinstance(builder_input, dict): return {"op_audit_trail_build_status": "invalid"}
    if "trail_id" not in builder_input: return {"op_audit_trail_build_status": "invalid"}
    return {"op_audit_trail_build_status": "built", "trail_id": builder_input.get("trail_id")}
