from typing import Any

def identity_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"identity_validator_status": "invalid"}
    return {"identity_validator_status": "validated"}
