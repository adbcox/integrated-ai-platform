from typing import Any

def rollout_entry_gate(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_entry_gate_status": "invalid"}
    return {"rollout_entry_gate_status": "ok"}
