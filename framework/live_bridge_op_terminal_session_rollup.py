from typing import Any
def rollup_terminal_session(rollup_input):
    if not isinstance(rollup_input, dict): return {"op_terminal_session_rollup_status": "invalid"}
    if "session_count" not in rollup_input: return {"op_terminal_session_rollup_status": "invalid"}
    return {"op_terminal_session_rollup_status": "rolled_up", "session_count": rollup_input.get("session_count")}
