from typing import Any

def proof_publication_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"proof_validator_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"proof_validator_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"proof_validator_status": "validation_context_failed"}
    return {"proof_validator_status": "ok"}
