from typing import Any

def reconciliation_summary(input_dict):
    if not isinstance(input_dict, dict):
        return {"reconciliation_summary_status": "invalid_input"}
    return {"reconciliation_summary_status": "valid"}
