from typing import Any
def rollup_terminal_console(rollup_input):
    if not isinstance(rollup_input, dict): return {"op_terminal_console_rollup_status": "invalid"}
    if "console_count" not in rollup_input: return {"op_terminal_console_rollup_status": "invalid"}
    return {"op_terminal_console_rollup_status": "rolled_up", "console_count": rollup_input.get("console_count")}
