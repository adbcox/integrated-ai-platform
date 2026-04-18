from typing import Any
def validate_exit_channel_identity(validation):
    if not isinstance(validation, dict): return {"exit_channel_identity_validation_status": "invalid"}
    if "operator_id" not in validation: return {"exit_channel_identity_validation_status": "invalid"}
    return {"exit_channel_identity_validation_status": "valid", "operator_id": validation.get("operator_id")}
