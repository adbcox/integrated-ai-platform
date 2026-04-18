from typing import Any
def build_terminal_summary(summary_input):
    if not isinstance(summary_input, dict): return {"op_terminal_summary_status": "invalid"}
    if "summary_id" not in summary_input: return {"op_terminal_summary_status": "invalid"}
    return {"op_terminal_summary_status": "built", "summary_id": summary_input.get("summary_id")}
