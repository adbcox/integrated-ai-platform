from typing import Any

def rollout_promotion_executor(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_promotion_executor_status": "invalid"}
    return {"rollout_promotion_executor_status": "ok"}
