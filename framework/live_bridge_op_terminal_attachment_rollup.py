from typing import Any
def rollup_terminal_attachment(rollup_input):
    if not isinstance(rollup_input, dict): return {"op_terminal_attachment_rollup_status": "invalid"}
    if "attachment_count" not in rollup_input: return {"op_terminal_attachment_rollup_status": "invalid"}
    return {"op_terminal_attachment_rollup_status": "rolled_up", "attachment_count": rollup_input.get("attachment_count")}
