from typing import Any

def runtime_admission_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_admission_validator_status": "invalid"}
    return {"runtime_admission_validator_status": "ok"}
