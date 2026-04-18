from typing import Any

def status_key_map_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"status_key_map_validator_status": "invalid_input"}
    return {"status_key_map_validator_status": "valid"}
