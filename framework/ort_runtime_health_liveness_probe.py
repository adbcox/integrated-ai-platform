from typing import Any

def health_liveness_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"health_liveness_status": "invalid"}
    return {"health_liveness_status": "alive"}
