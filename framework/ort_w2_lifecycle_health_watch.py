from typing import Any

def lifecycle_health_watch(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_health_watch_status": "invalid"}
    return {"lifecycle_health_watch_status": "ok"}
