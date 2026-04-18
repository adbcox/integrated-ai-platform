from typing import Any

def reconciliation_finalizer(input_dict):
    if not isinstance(input_dict, dict):
        return {"reconciliation_finalizer_status": "invalid_input"}
    return {"reconciliation_finalizer_status": "valid"}
