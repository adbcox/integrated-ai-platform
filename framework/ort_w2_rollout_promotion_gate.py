from typing import Any

def rollout_promotion_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_promotion_gate_status": "invalid"}
    return {"rollout_promotion_gate_status": "ok"}
