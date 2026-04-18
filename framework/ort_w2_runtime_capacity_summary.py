from typing import Any

def runtime_capacity_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_capacity_summary_status": "invalid"}
    return {"runtime_capacity_summary_status": "ok"}
