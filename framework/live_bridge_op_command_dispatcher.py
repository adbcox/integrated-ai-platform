from typing import Any
def dispatch_command(dispatch_input):
    if not isinstance(dispatch_input, dict): return {"op_command_dispatch_status": "invalid"}
    if "dispatch_target" not in dispatch_input: return {"op_command_dispatch_status": "invalid"}
    return {"op_command_dispatch_status": "dispatched", "dispatch_target": dispatch_input.get("dispatch_target")}
