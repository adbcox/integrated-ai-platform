from typing import Any

def ingress_health_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"ingress_health_status": "invalid"}
    return {"ingress_health_status": "healthy"}
