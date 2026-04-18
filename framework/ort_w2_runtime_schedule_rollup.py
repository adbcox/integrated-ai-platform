from typing import Any

def runtime_schedule_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_schedule_rollup_status": "invalid"}
    return {"runtime_schedule_rollup_status": "ok"}
