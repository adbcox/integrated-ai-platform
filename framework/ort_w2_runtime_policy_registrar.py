from typing import Any

def runtime_policy_registrar(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_policy_registrar_status": "invalid"}
    return {"runtime_policy_registrar_status": "ok"}
