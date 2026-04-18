from typing import Any

def resource_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"resource_validator_status": "invalid"}
    return {"resource_validator_status": "ok"}
