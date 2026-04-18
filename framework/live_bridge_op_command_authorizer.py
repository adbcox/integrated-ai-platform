from typing import Any
def authorize_command(auth_input):
    if not isinstance(auth_input, dict): return {"op_command_authorization_status": "invalid"}
    if "op_scope_bind_status" not in auth_input or auth_input.get("op_scope_bind_status") != "bound": return {"op_command_authorization_status": "unauthorized"}
    if "op_backpressure_status" not in auth_input or auth_input.get("op_backpressure_status") == "exceeded": return {"op_command_authorization_status": "unauthorized"}
    return {"op_command_authorization_status": "authorized"}
