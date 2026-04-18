from typing import Any
def validate_confirmation(validation):
    if not isinstance(validation, dict): return {"op_confirmation_validation_status": "invalid"}
    if validation.get("op_confirmation_receive_status") != "received": return {"op_confirmation_validation_status": "invalid"}
    return {"op_confirmation_validation_status": "valid", "confirmation_response": validation.get("confirmation_response")}
