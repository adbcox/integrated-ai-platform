from typing import Any

def deployment_startup_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"deployment_startup_status": "invalid"}
    return {"deployment_startup_status": "started"}
