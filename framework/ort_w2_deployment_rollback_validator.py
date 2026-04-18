from typing import Any

def deployment_rollback_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_rollback_validator_status": "invalid"}
    return {"deployment_rollback_validator_status": "ok"}
