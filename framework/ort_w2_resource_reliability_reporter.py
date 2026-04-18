from typing import Any

def resource_reliability_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"resource_reliability_reporter_status": "invalid"}
    return {"resource_reliability_reporter_status": "ok"}
