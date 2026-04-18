from typing import Any

def obs_bridge_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"obs_bridge_rollup_status": "invalid"}
    return {"obs_bridge_rollup_status": "ok"}
