from typing import Any

def helper_count_registry(input_dict):
    if not isinstance(input_dict, dict):
        return {"helper_count_registry_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"helper_count_registry_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"helper_count_registry_status": "validation_context_failed"}
    return {"helper_count_registry_status": "ok"}
