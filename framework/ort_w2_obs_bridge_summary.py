from typing import Any

def obs_bridge_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"obs_bridge_summary_status": "invalid"}
    return {"obs_bridge_summary_status": "ok"}
