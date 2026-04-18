from typing import Any

def runtime_slo_stability_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_slo_stability_gate_status": "invalid"}
    return {"runtime_slo_stability_gate_status": "ok"}
