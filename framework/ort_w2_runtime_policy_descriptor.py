from typing import Any

def runtime_policy_descriptor(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_policy_descriptor_status": "invalid"}
    return {"runtime_policy_descriptor_status": "ok"}
