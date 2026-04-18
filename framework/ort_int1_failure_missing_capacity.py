from typing import Any

def failure_missing_capacity(input_dict):
    if not isinstance(input_dict, dict):
        return {"failure_missing_capacity_status": "invalid_input"}
    return {"failure_missing_capacity_status": "valid"}
