from typing import Any

def seal_token_registry(input_dict):
    if not isinstance(input_dict, dict):
        return {"seal_token_registry_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"seal_token_registry_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"seal_token_registry_status": "validation_context_failed"}
    return {"seal_token_registry_status": "ok"}
