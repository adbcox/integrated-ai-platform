from typing import Any

def contract_health_watch(input_dict):
    if not isinstance(input_dict, dict):
        return {"contract_health_watch_status": "invalid_input"}
    return {"contract_health_watch_status": "valid"}
