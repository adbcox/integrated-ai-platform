from typing import Any

def rollout_canary_executor(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_canary_executor_status": "invalid"}
    return {"rollout_canary_executor_status": "ok"}
