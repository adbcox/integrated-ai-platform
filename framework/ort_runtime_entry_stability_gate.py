from typing import Any

def entry_stability_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"entry_stability_gate_status": "invalid"}
    return {"entry_stability_gate_status": "stable"}
