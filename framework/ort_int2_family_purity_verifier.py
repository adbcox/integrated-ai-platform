from typing import Any

def family_purity_verifier(input_dict):
    if not isinstance(input_dict, dict):
        return {"family_purity_verifier_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"family_purity_verifier_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"family_purity_verifier_status": "validation_context_failed"}
    return {"family_purity_verifier_status": "ok"}
