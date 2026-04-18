from typing import Any

def config_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"config_validator_status": "invalid"}
    return {"config_validator_status": "validated"}
