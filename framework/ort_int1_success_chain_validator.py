from typing import Any

def success_chain_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"success_chain_validator_status": "invalid_input"}
    return {"success_chain_validator_status": "valid"}
