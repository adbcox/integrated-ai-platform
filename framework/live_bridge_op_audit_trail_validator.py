from typing import Any
def validate_audit_trail(validation):
    if not isinstance(validation, dict): return {"op_audit_trail_validation_status": "invalid"}
    if validation.get("op_audit_trail_build_status") != "built": return {"op_audit_trail_validation_status": "invalid"}
    return {"op_audit_trail_validation_status": "valid", "trail_id": validation.get("trail_id")}
