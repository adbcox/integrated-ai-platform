from typing import Any

def environment_liveness_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"environment_liveness_status": "invalid"}
    return {"environment_liveness_status": "alive"}
