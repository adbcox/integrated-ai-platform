from typing import Any

def lifecycle_terminate_controller(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_terminate_controller_status": "invalid"}
    return {"lifecycle_terminate_controller_status": "ok"}
