from typing import Any

def exact_count_auditor(input_dict):
    if not isinstance(input_dict, dict):
        return {"exact_count_auditor_status": "invalid_input"}
    return {"exact_count_auditor_status": "valid"}
