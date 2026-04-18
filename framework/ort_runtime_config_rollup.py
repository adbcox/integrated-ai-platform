from typing import Any

def config_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"config_rollup_status": "invalid"}
    return {"config_rollup_status": "rolled_up"}
