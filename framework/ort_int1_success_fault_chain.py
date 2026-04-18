from typing import Any

def success_fault_chain(input_dict):
    if not isinstance(input_dict, dict):
        return {"success_fault_chain_status": "invalid_input"}
    return {"success_fault_chain_status": "valid"}
