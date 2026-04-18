from typing import Any

def entry_preflight_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"entry_preflight_gate_status": "invalid"}
    return {"entry_preflight_gate_status": "cleared"}
