from typing import Any

def fault_retry_controller(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_retry_controller_status": "invalid"}
    return {"fault_retry_controller_status": "ok"}
