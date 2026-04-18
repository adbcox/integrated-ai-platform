from typing import Any

def lifecycle_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_summary_status": "invalid"}
    return {"lifecycle_summary_status": "ok"}
