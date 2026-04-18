from typing import Any

def environment_health_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"environment_health_status": "invalid"}
    return {"environment_health_status": "healthy"}
