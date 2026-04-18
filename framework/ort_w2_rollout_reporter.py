from typing import Any

def rollout_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_reporter_status": "invalid"}
    return {"rollout_reporter_status": "ok"}
