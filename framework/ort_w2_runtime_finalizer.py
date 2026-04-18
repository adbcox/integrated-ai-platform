from typing import Any

def runtime_finalizer(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_finalizer_status": "invalid"}
    return {"runtime_finalizer_status": "ok"}
