from typing import Any

def lifecycle_state_transition_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_state_transition_validator_status": "invalid"}
    return {"lifecycle_state_transition_validator_status": "ok"}
