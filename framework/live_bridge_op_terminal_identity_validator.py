from typing import Any
def validate_identity(resolution):
    if not isinstance(resolution, dict):
        return {"op_identity_validation_status": "invalid"}
    if resolution.get("op_identity_resolution_status") != "resolved":
        return {"op_identity_validation_status": "invalid"}
    return {"op_identity_validation_status": "valid", "operator_id": resolution.get("operator_id")}
