from typing import Any

def fault_auditor(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_auditor_status": "invalid"}
    return {"fault_auditor_status": "ok"}
