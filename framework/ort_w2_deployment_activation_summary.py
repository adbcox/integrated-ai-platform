from typing import Any

def deployment_activation_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_activation_summary_status": "invalid"}
    return {"deployment_activation_summary_status": "ok"}
