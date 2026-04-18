from typing import Any
def seal_terminal_closure_layer(seal_input):
    if not isinstance(seal_input, dict): return {"op_terminal_closure_layer_seal_status": "invalid"}
    if seal_input.get("op_terminal_closure_completion_report_status") != "complete": return {"op_terminal_closure_layer_seal_status": "invalid"}
    if seal_input.get("op_terminal_closure_layer_finalization_status") != "finalized": return {"op_terminal_closure_layer_seal_status": "invalid"}
    if seal_input.get("operator_terminal_seal_status") != "sealed": return {"op_terminal_closure_layer_seal_status": "invalid"}
    return {"op_terminal_closure_layer_seal_status": "sealed"}
