from typing import Any

def lifecycle_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_reporter_status": "invalid"}
    return {"lifecycle_reporter_status": "ok"}
