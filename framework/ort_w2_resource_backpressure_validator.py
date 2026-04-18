from typing import Any

def resource_backpressure_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"resource_backpressure_validator_status": "invalid"}
    return {"resource_backpressure_validator_status": "ok"}
