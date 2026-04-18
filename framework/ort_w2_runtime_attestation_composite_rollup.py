from typing import Any

def runtime_attestation_composite_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_attestation_composite_rollup_status": "invalid"}
    return {"runtime_attestation_composite_rollup_status": "ok"}
