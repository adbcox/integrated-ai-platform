from typing import Any

def obs_bridge_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"obs_bridge_reporter_status": "invalid"}
    return {"obs_bridge_reporter_status": "ok"}
