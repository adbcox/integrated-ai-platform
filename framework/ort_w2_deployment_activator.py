from typing import Any

def deployment_activator(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_activator_status": "invalid"}
    return {"deployment_activator_status": "ok"}
