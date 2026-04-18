from typing import Any
def validate_heartbeat(validation):
    if not isinstance(validation, dict): return {"op_heartbeat_validation_status": "invalid"}
    if validation.get("op_heartbeat_receive_status") != "received": return {"op_heartbeat_validation_status": "invalid"}
    return {"op_heartbeat_validation_status": "valid", "heartbeat_id": validation.get("heartbeat_id")}
