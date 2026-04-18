from typing import Any

def deployment_activation_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_activation_reporter_status": "invalid"}
    return {"deployment_activation_reporter_status": "ok"}
