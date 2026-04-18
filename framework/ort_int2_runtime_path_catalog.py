from typing import Any

def runtime_path_catalog(input_dict):
    if not isinstance(input_dict, dict):
        return {"runtime_path_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"runtime_path_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"runtime_path_status": "validation_context_failed"}
    return {"runtime_path_status": "ok"}
