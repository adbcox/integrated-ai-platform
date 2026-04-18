from typing import Any

def environment_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"environment_validator_status": "invalid"}
    return {"environment_validator_status": "validated"}
