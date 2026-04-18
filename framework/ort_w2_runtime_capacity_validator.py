from typing import Any

def runtime_capacity_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_capacity_validator_status": "invalid"}
    return {"runtime_capacity_validator_status": "ok"}
