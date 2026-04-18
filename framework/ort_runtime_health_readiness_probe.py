from typing import Any

def health_readiness_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"health_readiness_status": "invalid"}
    return {"health_readiness_status": "ready"}
