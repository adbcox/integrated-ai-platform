from typing import Any

def runtime_policy_enforcement_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_policy_enforcement_validator_status": "invalid"}
    return {"runtime_policy_enforcement_validator_status": "ok"}
