from typing import Any
def validate_exit_quota(validation):
    if not isinstance(validation, dict): return {"exit_quota_validation_status": "invalid"}
    if validation.get("exit_quota_track_status") != "tracked": return {"exit_quota_validation_status": "invalid"}
    return {"exit_quota_validation_status": "valid", "quota_id": validation.get("quota_id")}
