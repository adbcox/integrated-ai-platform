from typing import Any

def success_chain_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"success_chain_gate_status": "invalid_input"}
    return {"success_chain_gate_status": "valid"}
