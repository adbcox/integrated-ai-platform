from typing import Any
def gate_terminal_entry(gate_input):
    if not isinstance(gate_input, dict): return {"op_terminal_entry_gate_status": "closed"}
    if gate_input.get("governed_fed_seal_status") != "sealed": return {"op_terminal_entry_gate_status": "closed"}
    if gate_input.get("adapter_layer_seal_status") != "sealed": return {"op_terminal_entry_gate_status": "closed"}
    if gate_input.get("obs_layer_seal_status") != "sealed": return {"op_terminal_entry_gate_status": "closed"}
    if gate_input.get("reconciliation_status") != "sealed": return {"op_terminal_entry_gate_status": "closed"}
    return {"op_terminal_entry_gate_status": "open"}
