from typing import Any

def obs_bridge_health_bridge(input_dict):
    if not isinstance(input_dict, dict):
        return {"obs_bridge_health_bridge_status": "invalid"}
    return {"obs_bridge_health_bridge_status": "ok"}
