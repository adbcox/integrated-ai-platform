from typing import Any

def terminal_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"terminal_gate_status": "invalid_input"}
    return {"terminal_gate_status": "valid"}
