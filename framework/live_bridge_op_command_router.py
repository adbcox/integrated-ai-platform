from typing import Any
def route_command(routing_input):
    if not isinstance(routing_input, dict): return {"op_command_route_status": "invalid"}
    if "target_handler" not in routing_input: return {"op_command_route_status": "invalid"}
    return {"op_command_route_status": "routed", "target_handler": routing_input.get("target_handler")}
