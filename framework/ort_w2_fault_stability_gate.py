from typing import Any

def fault_stability_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_stability_gate_status": "invalid"}
    return {"fault_stability_gate_status": "ok"}
