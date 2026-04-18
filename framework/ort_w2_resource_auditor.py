from typing import Any

def resource_auditor(input_dict):
    if not isinstance(input_dict, dict):
        return {"resource_auditor_status": "invalid"}
    return {"resource_auditor_status": "ok"}
