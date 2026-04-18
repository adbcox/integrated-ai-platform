from typing import Any

def resource_quota_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"resource_quota_validator_status": "invalid"}
    return {"resource_quota_validator_status": "ok"}
