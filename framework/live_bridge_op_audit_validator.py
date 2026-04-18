from typing import Any
def validate_audit(validation):
    if not isinstance(validation, dict): return {"op_audit_validation_status": "invalid"}
    if "audit_id" not in validation: return {"op_audit_validation_status": "invalid"}
    return {"op_audit_validation_status": "valid", "audit_id": validation.get("audit_id")}
