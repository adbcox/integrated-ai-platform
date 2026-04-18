from typing import Any

def proof_aggregation_descriptor(input_dict):
    if not isinstance(input_dict, dict):
        return {"proof_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"proof_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"proof_status": "validation_context_failed"}
    return {"proof_status": "ok"}
