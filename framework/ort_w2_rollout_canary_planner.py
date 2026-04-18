from typing import Any

def rollout_canary_planner(input_dict):
    if not isinstance(input_dict, dict):
        return {"rollout_canary_planner_status": "invalid"}
    return {"rollout_canary_planner_status": "ok"}
