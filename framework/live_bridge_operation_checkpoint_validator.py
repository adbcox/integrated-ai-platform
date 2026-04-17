from typing import Any

def validate_operation_checkpoint(checkpoint: dict[str, Any], tracking: dict[str, Any], validator_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(checkpoint, dict) or not isinstance(tracking, dict) or not isinstance(validator_config, dict):
        return {"checkpoint_validation_status": "invalid_input", "validated_checkpoint_id": None, "validated_operation_id": None}
    c_ok = checkpoint.get("checkpoint_status") == "written"
    t_ok = tracking.get("execution_tracking_status") == "tracking"
    if not c_ok:
        return {"checkpoint_validation_status": "no_checkpoint", "validated_checkpoint_id": None, "validated_operation_id": None}
    if c_ok and not t_ok:
        return {"checkpoint_validation_status": "no_tracking", "validated_checkpoint_id": None, "validated_operation_id": None}
    return {"checkpoint_validation_status": "valid", "validated_checkpoint_id": checkpoint.get("checkpoint_id"), "validated_operation_id": checkpoint.get("checkpoint_operation_id")} if c_ok and t_ok else {"checkpoint_validation_status": "invalid_input", "validated_checkpoint_id": None, "validated_operation_id": None}
