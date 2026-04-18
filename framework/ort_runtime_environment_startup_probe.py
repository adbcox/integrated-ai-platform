from typing import Any

def environment_startup_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"environment_startup_status": "invalid"}
    return {"environment_startup_status": "started"}
