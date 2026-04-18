from typing import Any

def identity_registrar(input_dict):
    if not isinstance(input_dict, dict):
        return {"identity_registrar_status": "invalid"}
    return {"identity_registrar_status": "registered"}
