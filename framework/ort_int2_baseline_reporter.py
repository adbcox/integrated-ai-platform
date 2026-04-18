from typing import Any

def baseline_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"baseline_reporter_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"baseline_reporter_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"baseline_reporter_status": "validation_context_failed"}
    return {"baseline_reporter_status": "ok"}
