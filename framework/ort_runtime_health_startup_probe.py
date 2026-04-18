from typing import Any

def health_startup_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"health_startup_status": "invalid"}
    return {"health_startup_status": "started"}
