from typing import Any

def identity_liveness_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"identity_liveness_status": "invalid"}
    return {"identity_liveness_status": "alive"}
