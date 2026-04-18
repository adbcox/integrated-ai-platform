from typing import Any

def rollout_stability_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_stability_gate_status": "invalid"}
    return {"rollout_stability_gate_status": "ok"}
