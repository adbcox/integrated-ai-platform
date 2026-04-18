from typing import Any
def gate_terminal_layer(gate_input):
    if not isinstance(gate_input, dict): return {"op_terminal_layer_gate_status": "closed"}
    if gate_input.get("op_terminal_entry_gate_status") != "open": return {"op_terminal_layer_gate_status": "closed"}
    return {"op_terminal_layer_gate_status": "open"}
