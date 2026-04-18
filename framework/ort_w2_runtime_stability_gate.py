from typing import Any

def runtime_stability_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_stability_gate_status": "invalid"}
    return {"runtime_stability_gate_status": "ok"}
