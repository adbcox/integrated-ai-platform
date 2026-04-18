from typing import Any
def seal_exit_integration_layer(seal_input):
    if not isinstance(seal_input, dict): return {"exit_integration_seal_status": "invalid"}
    if seal_input.get("exit_integration_completion_report_status") != "complete": return {"exit_integration_seal_status": "invalid"}
    if seal_input.get("exit_integration_layer_finalization_status") != "finalized": return {"exit_integration_seal_status": "invalid"}
    if seal_input.get("exit_entry_gate_status") != "open": return {"exit_integration_seal_status": "invalid"}
    return {"exit_integration_seal_status": "sealed"}
