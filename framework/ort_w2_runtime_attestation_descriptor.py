from typing import Any

def runtime_attestation_descriptor(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_attestation_descriptor_status": "invalid"}
    return {"runtime_attestation_descriptor_status": "ok"}
