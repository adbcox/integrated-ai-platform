from typing import Any
def validate_command_quota(validation):
    if not isinstance(validation, dict): return {"op_quota_validation_status": "invalid"}
    if validation.get("op_quota_track_status") != "tracked": return {"op_quota_validation_status": "invalid"}
    return {"op_quota_validation_status": "valid", "quota_id": validation.get("quota_id")}
