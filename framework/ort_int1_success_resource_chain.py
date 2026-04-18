from typing import Any

def success_resource_chain(input_dict):
    if not isinstance(input_dict, dict):
        return {"success_resource_chain_status": "invalid_input"}
    return {"success_resource_chain_status": "valid"}
