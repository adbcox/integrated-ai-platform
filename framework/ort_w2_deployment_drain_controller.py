from typing import Any

def deployment_drain_controller(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_drain_controller_status": "invalid"}
    return {"deployment_drain_controller_status": "ok"}
