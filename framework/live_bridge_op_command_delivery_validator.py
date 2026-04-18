from typing import Any
def validate_command_delivery(validation):
    if not isinstance(validation, dict): return {"op_delivery_validation_status": "invalid"}
    if validation.get("op_delivery_track_status") != "tracked": return {"op_delivery_validation_status": "invalid"}
    return {"op_delivery_validation_status": "valid", "delivery_id": validation.get("delivery_id")}
