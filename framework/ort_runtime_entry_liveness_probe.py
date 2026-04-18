from typing import Any

def entry_liveness_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"entry_liveness_status": "invalid"}
    return {"entry_liveness_status": "alive"}
