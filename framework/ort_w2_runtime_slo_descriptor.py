from typing import Any

def runtime_slo_descriptor(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_slo_descriptor_status": "invalid"}
    return {"runtime_slo_descriptor_status": "ok"}
