from typing import Any

def runtime_schedule_plan_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_schedule_plan_validator_status": "invalid"}
    return {"runtime_schedule_plan_validator_status": "ok"}
