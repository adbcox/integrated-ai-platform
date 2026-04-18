from typing import Any

def config_startup_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"config_startup_status": "invalid"}
    return {"config_startup_status": "started"}
