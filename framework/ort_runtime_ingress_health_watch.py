from typing import Any

def ingress_health_watch(input_dict):
    if not isinstance(input_dict, dict):
        return {"ingress_health_watch_status": "invalid"}
    return {"ingress_health_watch_status": "watched"}
