from typing import Any

def count_preflight_verifier(input_dict):
    if not isinstance(input_dict, dict):
        return {"count_preflight_verifier_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"count_preflight_verifier_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"count_preflight_verifier_status": "validation_context_failed"}
    return {"count_preflight_verifier_status": "ok"}
