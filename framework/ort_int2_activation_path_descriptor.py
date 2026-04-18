from typing import Any

def activation_path_descriptor(input_dict):
    if not isinstance(input_dict, dict):
        return {"activation_path_descriptor_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"activation_path_descriptor_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"activation_path_descriptor_status": "validation_context_failed"}
    return {"activation_path_descriptor_status": "ok"}
