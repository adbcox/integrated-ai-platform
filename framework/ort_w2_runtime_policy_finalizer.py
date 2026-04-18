from typing import Any

def runtime_policy_finalizer(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_policy_finalizer_status": "invalid"}
    return {"runtime_policy_finalizer_status": "ok"}
