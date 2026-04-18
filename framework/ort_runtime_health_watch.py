from typing import Any

def health_watch(input_dict):
    if not isinstance(input_dict, dict):
        return {"health_watch_status": "invalid"}
    return {"health_watch_status": "watched"}
