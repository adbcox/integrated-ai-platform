from typing import Any
def gate_exit_entry(gate_input):
    if not isinstance(gate_input, dict): return {"exit_entry_gate_status": "closed"}
    if gate_input.get("governed_fed_seal_status") != "sealed": return {"exit_entry_gate_status": "closed"}
    if gate_input.get("adapter_layer_seal_status") != "sealed": return {"exit_entry_gate_status": "closed"}
    if gate_input.get("obs_layer_seal_status") != "sealed": return {"exit_entry_gate_status": "closed"}
    if gate_input.get("operator_terminal_seal_status") != "sealed": return {"exit_entry_gate_status": "closed"}
    return {"exit_entry_gate_status": "open"}
