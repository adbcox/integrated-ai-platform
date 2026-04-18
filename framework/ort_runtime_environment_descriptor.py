from typing import Any

def environment_descriptor(input_dict):
    if not isinstance(input_dict, dict):
        return {"environment_descriptor_status": "invalid"}
    return {"environment_descriptor_status": "described"}
