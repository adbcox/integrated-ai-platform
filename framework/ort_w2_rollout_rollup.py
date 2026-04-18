from typing import Any

def rollout_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_rollup_status": "invalid"}
    return {"rollout_rollup_status": "ok"}
