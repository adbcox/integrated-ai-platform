from typing import Any

def runtime_schedule_planner(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_schedule_planner_status": "invalid"}
    return {"runtime_schedule_planner_status": "ok"}
