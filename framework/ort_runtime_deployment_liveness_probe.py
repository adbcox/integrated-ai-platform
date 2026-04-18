from typing import Any

def deployment_liveness_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_liveness_status": "invalid"}
    return {"deployment_liveness_status": "alive"}
