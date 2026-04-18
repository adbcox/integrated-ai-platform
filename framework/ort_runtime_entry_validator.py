from typing import Any

def entry_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"entry_validator_status": "invalid"}
    return {"entry_validator_status": "validated"}
