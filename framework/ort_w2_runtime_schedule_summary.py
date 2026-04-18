from typing import Any

def runtime_schedule_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_schedule_summary_status": "invalid"}
    return {"runtime_schedule_summary_status": "ok"}
