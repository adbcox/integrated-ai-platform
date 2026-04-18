from typing import Any

def runtime_capacity_descriptor(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_capacity_descriptor_status": "invalid"}
    return {"runtime_capacity_descriptor_status": "ok"}
