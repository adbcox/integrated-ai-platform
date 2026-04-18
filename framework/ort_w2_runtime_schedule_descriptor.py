from typing import Any

def runtime_schedule_descriptor(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_schedule_descriptor_status": "invalid"}
    return {"runtime_schedule_descriptor_status": "ok"}
