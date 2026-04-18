from typing import Any

def runtime_completion_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_completion_reporter_status": "invalid"}
    return {"runtime_completion_reporter_status": "ok"}
