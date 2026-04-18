from typing import Any

def runtime_reliability_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_reliability_gate_status": "invalid"}
    return {"runtime_reliability_gate_status": "ok"}
