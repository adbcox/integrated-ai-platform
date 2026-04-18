from typing import Any

def path_triplet_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"path_triplet_reporter_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"path_triplet_reporter_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"path_triplet_reporter_status": "validation_context_failed"}
    return {"path_triplet_reporter_status": "ok"}
