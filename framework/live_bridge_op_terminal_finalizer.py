from typing import Any
def finalize_terminal(finalizer_input):
    if not isinstance(finalizer_input, dict): return {"op_terminal_finalization_status": "invalid"}
    if finalizer_input.get("op_terminal_layer_gate_status") != "open": return {"op_terminal_finalization_status": "invalid"}
    return {"op_terminal_finalization_status": "finalized"}
