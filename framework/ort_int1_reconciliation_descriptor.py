from typing import Any

def reconciliation_descriptor(input_dict):
    if not isinstance(input_dict, dict):
        return {"reconciliation_descriptor_status": "invalid_input"}
    return {"reconciliation_descriptor_status": "valid"}
