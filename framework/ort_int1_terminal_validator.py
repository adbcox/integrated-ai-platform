from typing import Any

def terminal_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"terminal_validator_status": "invalid_input"}
    return {"terminal_validator_status": "valid"}
