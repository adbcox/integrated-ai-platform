from typing import Any

def identity_health_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"identity_health_status": "invalid"}
    return {"identity_health_status": "healthy"}
