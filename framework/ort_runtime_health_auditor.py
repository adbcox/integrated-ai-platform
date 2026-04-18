from typing import Any

def health_auditor(input_dict):
    if not isinstance(input_dict, dict):
        return {"health_audit_status": "invalid"}
    return {"health_audit_status": "audited"}
