from typing import Any

def runtime_admission_controller(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_admission_controller_status": "invalid"}
    return {"runtime_admission_controller_status": "ok"}
