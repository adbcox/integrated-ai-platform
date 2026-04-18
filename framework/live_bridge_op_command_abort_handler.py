from typing import Any
def handle_command_abort(abort_input):
    if not isinstance(abort_input, dict): return {"op_abort_handle_status": "invalid"}
    if "abort_reason" not in abort_input: return {"op_abort_handle_status": "invalid"}
    return {"op_abort_handle_status": "handled", "abort_reason": abort_input.get("abort_reason")}
