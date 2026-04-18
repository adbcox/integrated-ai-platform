from typing import Any

def lifecycle_stop_controller(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_stop_controller_status": "invalid"}
    return {"lifecycle_stop_controller_status": "ok"}
