from typing import Any
def gate_exit_integration_entry(gate_input):
    if not isinstance(gate_input, dict): return {"exit_integration_entry_gate_status": "closed"}
    if gate_input.get("exit_entry_gate_status") != "open": return {"exit_integration_entry_gate_status": "closed"}
    if gate_input.get("op_terminal_closure_layer_seal_status") != "sealed": return {"exit_integration_entry_gate_status": "closed"}
    if gate_input.get("op_audit_cp_layer_seal_status") != "sealed": return {"exit_integration_entry_gate_status": "closed"}
    if gate_input.get("reconciliation_status") != "sealed": return {"exit_integration_entry_gate_status": "closed"}
    return {"exit_integration_entry_gate_status": "open"}
