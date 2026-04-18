from typing import Any

def commit_chain_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"commit_chain_validator_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"commit_chain_validator_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"commit_chain_validator_status": "validation_context_failed"}
    return {"commit_chain_validator_status": "ok"}
