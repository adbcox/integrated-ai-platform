from typing import Any

def config_health_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"config_health_status": "invalid"}
    return {"config_health_status": "healthy"}
