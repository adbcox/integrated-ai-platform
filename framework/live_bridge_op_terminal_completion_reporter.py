from typing import Any
def report_terminal_completion(report_input):
    if not isinstance(report_input, dict): return {"op_terminal_completion_report_status": "invalid"}
    if report_input.get("op_terminal_finalization_status") != "finalized": return {"op_terminal_completion_report_status": "invalid"}
    return {"op_terminal_completion_report_status": "complete"}
