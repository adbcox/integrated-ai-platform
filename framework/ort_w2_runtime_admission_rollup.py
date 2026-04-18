from typing import Any

def runtime_admission_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_admission_rollup_status": "invalid"}
    return {"runtime_admission_rollup_status": "ok"}
