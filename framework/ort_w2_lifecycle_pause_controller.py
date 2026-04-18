from typing import Any

def lifecycle_pause_controller(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_pause_controller_status": "invalid"}
    return {"lifecycle_pause_controller_status": "ok"}
