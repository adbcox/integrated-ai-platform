from typing import Any

def runtime_admission_denial_recorder(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_admission_denial_recorder_status": "invalid"}
    return {"runtime_admission_denial_recorder_status": "ok"}
