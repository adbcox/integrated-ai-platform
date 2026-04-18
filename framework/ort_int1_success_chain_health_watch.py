from typing import Any

def success_chain_health_watch(input_dict):
    if not isinstance(input_dict, dict):
        return {"success_chain_health_watch_status": "invalid_input"}
    return {"success_chain_health_watch_status": "valid"}
