from typing import Any

def ingress_schema_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"ingress_schema_status": "invalid"}
    return {"ingress_schema_status": "validated"}
