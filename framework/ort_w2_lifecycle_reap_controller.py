from typing import Any

def lifecycle_reap_controller(input_dict):
    if not isinstance(input_dict, dict):
        return {"lifecycle_reap_controller_status": "invalid"}
    return {"lifecycle_reap_controller_status": "ok"}
