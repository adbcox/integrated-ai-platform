from typing import Any
def rollup_command_health(rollup_input):
    if not isinstance(rollup_input, dict): return {"op_command_health_rollup_status": "invalid"}
    if rollup_input.get("op_command_health_watch_status") != "watching": return {"op_command_health_rollup_status": "invalid"}
    return {"op_command_health_rollup_status": "rolled_up", "health_id": rollup_input.get("health_id")}
