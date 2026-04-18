from typing import Any

def fault_retry_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_retry_validator_status": "invalid"}
    return {"fault_retry_validator_status": "ok"}
