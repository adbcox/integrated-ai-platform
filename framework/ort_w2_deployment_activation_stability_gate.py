from typing import Any

def deployment_activation_stability_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_activation_stability_gate_status": "invalid"}
    return {"deployment_activation_stability_gate_status": "ok"}
