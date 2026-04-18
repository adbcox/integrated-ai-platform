from typing import Any

def runtime_schedule_registrar(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_schedule_registrar_status": "invalid"}
    return {"runtime_schedule_registrar_status": "ok"}
