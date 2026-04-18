from typing import Any

def runtime_policy_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_policy_reporter_status": "invalid"}
    return {"runtime_policy_reporter_status": "ok"}
