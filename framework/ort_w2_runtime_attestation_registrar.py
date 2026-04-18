from typing import Any

def runtime_attestation_registrar(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_attestation_registrar_status": "invalid"}
    return {"runtime_attestation_registrar_status": "ok"}
