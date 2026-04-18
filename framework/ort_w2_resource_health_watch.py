from typing import Any

def resource_health_watch(input_dict):
    if not isinstance(input_dict, dict):
        return {"resource_health_watch_status": "invalid"}
    return {"resource_health_watch_status": "ok"}
