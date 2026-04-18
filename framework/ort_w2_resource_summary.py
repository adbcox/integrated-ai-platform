from typing import Any

def resource_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"resource_summary_status": "invalid"}
    return {"resource_summary_status": "ok"}
