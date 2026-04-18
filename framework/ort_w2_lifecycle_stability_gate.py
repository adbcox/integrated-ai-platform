from typing import Any

def lifecycle_stability_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_stability_gate_status": "invalid"}
    return {"lifecycle_stability_gate_status": "ok"}
