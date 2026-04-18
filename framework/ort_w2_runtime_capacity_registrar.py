from typing import Any

def runtime_capacity_registrar(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_capacity_registrar_status": "invalid"}
    return {"runtime_capacity_registrar_status": "ok"}
