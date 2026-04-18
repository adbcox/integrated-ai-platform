from typing import Any

def control_plane_builder(input_dict):
    if not isinstance(input_dict, dict):
        return {"control_plane_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"control_plane_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"control_plane_status": "validation_context_failed"}
    return {"control_plane_status": "ok"}
