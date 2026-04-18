from typing import Any

def runtime_slo_registrar(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_slo_registrar_status": "invalid"}
    return {"runtime_slo_registrar_status": "ok"}
