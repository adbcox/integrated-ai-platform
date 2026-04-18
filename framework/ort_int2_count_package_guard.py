from typing import Any

def count_package_guard(input_dict):
    if not isinstance(input_dict, dict):
        return {"count_guard_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"count_guard_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"count_guard_status": "validation_context_failed"}
    return {"count_guard_status": "ok"}
