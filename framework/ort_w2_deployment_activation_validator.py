from typing import Any

def deployment_activation_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_activation_validator_status": "invalid"}
    return {"deployment_activation_validator_status": "ok"}
