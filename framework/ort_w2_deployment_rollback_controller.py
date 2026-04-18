from typing import Any

def deployment_rollback_controller(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_rollback_controller_status": "invalid"}
    return {"deployment_rollback_controller_status": "ok"}
