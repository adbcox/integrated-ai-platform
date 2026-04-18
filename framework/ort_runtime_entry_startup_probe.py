from typing import Any

def entry_startup_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"entry_startup_status": "invalid"}
    return {"entry_startup_status": "started"}
