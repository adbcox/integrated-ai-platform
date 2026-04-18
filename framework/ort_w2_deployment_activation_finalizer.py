from typing import Any

def deployment_activation_finalizer(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_activation_finalizer_status": "invalid"}
    return {"deployment_activation_finalizer_status": "ok"}
