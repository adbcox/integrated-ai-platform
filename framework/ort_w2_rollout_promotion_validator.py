from typing import Any

def rollout_promotion_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_promotion_validator_status": "invalid"}
    return {"rollout_promotion_validator_status": "ok"}
