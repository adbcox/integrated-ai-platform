from typing import Any
def validate_exit_ingress(validation):
    if not isinstance(validation, dict): return {"exit_ingress_validation_status": "invalid"}
    if validation.get("exit_ingress_audit_status") != "audited": return {"exit_ingress_validation_status": "invalid"}
    return {"exit_ingress_validation_status": "valid", "audit_id": validation.get("audit_id")}
