from typing import Any

def health_startup_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"health_startup_validator_status": "invalid"}
    return {"health_startup_validator_status": "validated"}
