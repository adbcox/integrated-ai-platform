from typing import Any

def fault_recovery_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_recovery_validator_status": "invalid"}
    return {"fault_recovery_validator_status": "ok"}
