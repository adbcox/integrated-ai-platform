from typing import Any

def rollout_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_summary_status": "invalid"}
    return {"rollout_summary_status": "ok"}
