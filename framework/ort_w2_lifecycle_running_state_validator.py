from typing import Any

def lifecycle_running_state_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_running_state_validator_status": "invalid"}
    return {"lifecycle_running_state_validator_status": "ok"}
