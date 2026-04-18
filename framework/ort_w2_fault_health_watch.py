from typing import Any

def fault_health_watch(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_health_watch_status": "invalid"}
    return {"fault_health_watch_status": "ok"}
