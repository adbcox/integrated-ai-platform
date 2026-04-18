from typing import Any
def seal_terminal_layer(seal_input):
    if not isinstance(seal_input, dict): return {"operator_terminal_seal_status": "invalid"}
    if seal_input.get("op_terminal_completion_report_status") != "complete": return {"operator_terminal_seal_status": "invalid"}
    if seal_input.get("op_terminal_layer_finalization_status") != "finalized": return {"operator_terminal_seal_status": "invalid"}
    return {"operator_terminal_seal_status": "sealed"}
