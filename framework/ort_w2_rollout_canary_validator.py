from typing import Any

def rollout_canary_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_canary_validator_status": "invalid"}
    return {"rollout_canary_validator_status": "ok"}
