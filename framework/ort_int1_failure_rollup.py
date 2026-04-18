from typing import Any

def failure_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"failure_rollup_status": "invalid_input"}
    return {"failure_rollup_status": "valid"}
