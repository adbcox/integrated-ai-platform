from typing import Any

def lifecycle_start_controller(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_start_controller_status": "invalid"}
    return {"lifecycle_start_controller_status": "ok"}
