from typing import Any

def lifecycle_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_rollup_status": "invalid"}
    return {"lifecycle_rollup_status": "ok"}
