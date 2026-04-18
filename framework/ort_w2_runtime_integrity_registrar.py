from typing import Any

def runtime_integrity_registrar(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_integrity_registrar_status": "invalid"}
    return {"runtime_integrity_registrar_status": "ok"}
