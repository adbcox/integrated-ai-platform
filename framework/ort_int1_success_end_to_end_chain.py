from typing import Any

def success_end_to_end_chain(input_dict):
    if not isinstance(input_dict, dict):
        return {"success_end_to_end_chain_status": "invalid_input"}
    return {"success_end_to_end_chain_status": "valid"}
