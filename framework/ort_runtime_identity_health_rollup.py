from typing import Any

def identity_health_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"identity_health_rollup_status": "invalid"}
    return {"identity_health_rollup_status": "rolled_up"}
