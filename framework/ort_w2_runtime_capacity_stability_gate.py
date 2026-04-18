from typing import Any

def runtime_capacity_stability_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_capacity_stability_gate_status": "invalid"}
    return {"runtime_capacity_stability_gate_status": "ok"}
