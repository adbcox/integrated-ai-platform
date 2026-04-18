from typing import Any

def health_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"health_rollup_status": "invalid"}
    return {"health_rollup_status": "rolled_up"}
