from typing import Any
def validate_command_retry(validation):
    if not isinstance(validation, dict): return {"op_retry_validation_status": "invalid"}
    if validation.get("op_retry_control_status") != "controlled": return {"op_retry_validation_status": "invalid"}
    return {"op_retry_validation_status": "valid", "retry_count": validation.get("retry_count")}
