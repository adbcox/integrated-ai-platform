from typing import Any

def health_liveness_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"health_liveness_validator_status": "invalid"}
    return {"health_liveness_validator_status": "validated"}
