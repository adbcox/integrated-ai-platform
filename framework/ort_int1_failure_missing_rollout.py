from typing import Any

def failure_missing_rollout(input_dict):
    if not isinstance(input_dict, dict):
        return {"failure_missing_rollout_status": "invalid_input"}
    return {"failure_missing_rollout_status": "valid"}
