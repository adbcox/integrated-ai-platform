from typing import Any

def fault_fallback_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"fault_fallback_validator_status": "invalid"}
    return {"fault_fallback_validator_status": "ok"}
