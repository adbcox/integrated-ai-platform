from typing import Any

def deployment_health_status(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_health_status": "invalid"}
    return {"deployment_health_status": "healthy"}
