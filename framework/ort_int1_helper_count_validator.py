from typing import Any

def helper_count_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"helper_count_validator_status": "invalid_input"}
    return {"helper_count_validator_status": "valid"}
