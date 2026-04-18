from typing import Any

def resource_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"resource_rollup_status": "invalid"}
    return {"resource_rollup_status": "ok"}
