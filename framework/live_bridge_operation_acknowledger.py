from typing import Any

def acknowledge_operation(completion: dict[str, Any], checkpoint_validation: dict[str, Any], ack_config: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(completion, dict) or not isinstance(checkpoint_validation, dict) or not isinstance(ack_config, dict):
        return {"acknowledgement_status": "invalid_input", "acked_operation_id": None, "ack_id": None, "ack_outcome": None}
    c_ok = completion.get("completion_status") == "completed"
    cv_ok = checkpoint_validation.get("checkpoint_validation_status") == "valid"
    if not c_ok:
        return {"acknowledgement_status": "not_completed", "acked_operation_id": None, "ack_id": None, "ack_outcome": None}
    if c_ok and not cv_ok:
        return {"acknowledgement_status": "no_checkpoint", "acked_operation_id": None, "ack_id": None, "ack_outcome": None}
    return {"acknowledgement_status": "acknowledged", "acked_operation_id": completion.get("completed_operation_id"), "ack_id": ack_config.get("ack_id", "ack-0001"), "ack_outcome": completion.get("completion_outcome")} if c_ok and cv_ok else {"acknowledgement_status": "invalid_input", "acked_operation_id": None, "ack_id": None, "ack_outcome": None}
