from typing import Any

def entry_health_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"entry_health_rollup_status": "invalid"}
    return {"entry_health_rollup_status": "rolled_up"}
