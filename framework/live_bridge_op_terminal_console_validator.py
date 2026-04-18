from typing import Any
def validate_console(registration):
    if not isinstance(registration, dict):
        return {"op_console_validation_status": "invalid"}
    if registration.get("op_console_registration_status") != "registered":
        return {"op_console_validation_status": "invalid"}
    return {"op_console_validation_status": "valid", "console_id": registration.get("console_id")}
