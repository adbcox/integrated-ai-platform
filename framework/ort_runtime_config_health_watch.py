from typing import Any

def config_health_watch(input_dict):
    if not isinstance(input_dict, dict):
        return {"config_health_watch_status": "invalid"}
    return {"config_health_watch_status": "watched"}
