from typing import Any

def metrics_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"metrics_rollup_status": "invalid_input"}
    return {"metrics_rollup_status": "valid"}
