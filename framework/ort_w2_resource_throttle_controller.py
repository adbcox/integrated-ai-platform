from typing import Any

def resource_throttle_controller(input_dict):
    if not isinstance(input_dict, dict):
        return {"resource_throttle_controller_status": "invalid"}
    return {"resource_throttle_controller_status": "ok"}
