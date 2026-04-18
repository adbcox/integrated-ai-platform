from typing import Any

def harness_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"harness_rollup_status": "invalid_input"}
    return {"harness_rollup_status": "valid"}
