from typing import Any

def config_health_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"config_health_rollup_status": "invalid"}
    return {"config_health_rollup_status": "rolled_up"}
