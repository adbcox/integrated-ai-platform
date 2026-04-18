from typing import Any

def rollout_rollback_executor(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_rollback_executor_status": "invalid"}
    return {"rollout_rollback_executor_status": "ok"}
