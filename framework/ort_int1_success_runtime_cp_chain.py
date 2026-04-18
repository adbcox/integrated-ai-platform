from typing import Any

def success_runtime_cp_chain(input_dict):
    if not isinstance(input_dict, dict):
        return {"success_runtime_cp_chain_status": "invalid_input"}
    return {"success_runtime_cp_chain_status": "valid"}
