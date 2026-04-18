from typing import Any

def ingress_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"ingress_validator_status": "invalid"}
    return {"ingress_validator_status": "validated"}
