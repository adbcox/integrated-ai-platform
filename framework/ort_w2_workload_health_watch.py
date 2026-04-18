from typing import Any

def workload_health_watch(input_dict):
    if not isinstance(input_dict, dict):
        return {"workload_health_watch_status": "invalid"}
    return {"workload_health_watch_status": "ok"}
