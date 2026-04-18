from typing import Any

def full_pipeline_completion_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"full_pipeline_reporter_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"full_pipeline_reporter_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"full_pipeline_reporter_status": "validation_context_failed"}
    return {"full_pipeline_reporter_status": "ok"}
