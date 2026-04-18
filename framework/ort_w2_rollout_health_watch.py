from typing import Any

def rollout_health_watch(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_health_watch_status": "invalid"}
    return {"rollout_health_watch_status": "ok"}
