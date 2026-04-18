from typing import Any

def runtime_health_watch(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_health_watch_status": "invalid"}
    return {"runtime_health_watch_status": "ok"}
