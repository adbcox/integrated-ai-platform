from typing import Any

def entry_health_probe(input_dict):
    if not isinstance(input_dict, dict):
        return {"entry_health_status": "invalid"}
    return {"entry_health_status": "healthy"}
