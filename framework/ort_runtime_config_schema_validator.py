from typing import Any

def config_schema_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"config_schema_status": "invalid"}
    return {"config_schema_status": "validated"}
