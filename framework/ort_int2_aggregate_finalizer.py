from typing import Any

def aggregate_finalizer(input_dict):
    if not isinstance(input_dict, dict):
        return {"aggregate_finalizer_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"aggregate_finalizer_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"aggregate_finalizer_status": "validation_context_failed"}
    return {"aggregate_finalizer_status": "ok"}
