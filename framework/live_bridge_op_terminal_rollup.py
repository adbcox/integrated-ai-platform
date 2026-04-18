from typing import Any
def rollup_terminal(rollup_input):
    if not isinstance(rollup_input, dict): return {"op_terminal_rollup_status": "invalid"}
    if "rollup_id" not in rollup_input: return {"op_terminal_rollup_status": "invalid"}
    return {"op_terminal_rollup_status": "rolled_up", "rollup_id": rollup_input.get("rollup_id")}
