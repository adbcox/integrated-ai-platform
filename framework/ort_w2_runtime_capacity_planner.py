from typing import Any

def runtime_capacity_planner(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_capacity_planner_status": "invalid"}
    return {"runtime_capacity_planner_status": "ok"}
