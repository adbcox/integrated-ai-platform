from typing import Any
def validate_exit_payload(validation):
    if not isinstance(validation, dict): return {"exit_payload_validation_status": "invalid"}
    if validation.get("exit_payload_encode_status") != "encoded": return {"exit_payload_validation_status": "invalid"}
    return {"exit_payload_validation_status": "valid", "payload_id": validation.get("payload_id")}
