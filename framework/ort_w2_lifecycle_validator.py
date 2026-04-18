from typing import Any

def lifecycle_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_validator_status": "invalid"}
    return {"lifecycle_validator_status": "ok"}
