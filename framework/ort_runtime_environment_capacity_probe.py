from typing import Any

def environment_capacity_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"environment_capacity_status": "invalid"}
    return {"environment_capacity_status": "capacitated"}
