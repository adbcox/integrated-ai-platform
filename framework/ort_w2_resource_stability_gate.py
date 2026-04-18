from typing import Any

def resource_stability_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"resource_stability_gate_status": "invalid"}
    return {"resource_stability_gate_status": "ok"}
