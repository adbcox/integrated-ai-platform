from typing import Any

def runtime_attestation_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_attestation_summary_status": "invalid"}
    return {"runtime_attestation_summary_status": "ok"}
