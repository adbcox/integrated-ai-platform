from typing import Any

def count_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"count_reporter_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"count_reporter_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"count_reporter_status": "validation_context_failed"}
    return {"count_reporter_status": "ok"}
