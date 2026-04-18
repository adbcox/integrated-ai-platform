from typing import Any
def rollup_terminal_session_validation(rollup_input):
    if not isinstance(rollup_input, dict): return {"op_terminal_session_validation_rollup_status": "invalid"}
    if "validation_count" not in rollup_input: return {"op_terminal_session_validation_rollup_status": "invalid"}
    return {"op_terminal_session_validation_rollup_status": "rolled_up", "validation_count": rollup_input.get("validation_count")}
