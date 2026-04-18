from typing import Any

def rollout_rollback_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_rollback_validator_status": "invalid"}
    return {"rollout_rollback_validator_status": "ok"}
