from typing import Any

def runtime_schedule_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_schedule_reporter_status": "invalid"}
    return {"runtime_schedule_reporter_status": "ok"}
