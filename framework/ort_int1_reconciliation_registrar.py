from typing import Any

def reconciliation_registrar(input_dict):
    if not isinstance(input_dict, dict):
        return {"reconciliation_registrar_status": "invalid_input"}
    return {"reconciliation_registrar_status": "valid"}
