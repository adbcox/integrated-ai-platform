from typing import Any

def min_bytes_guard_catalog(input_dict):
    if not isinstance(input_dict, dict):
        # HARD GATE: Invalid input type
        return {"min_bytes_guard_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            # HARD GATE: Upstream seal not in sealed state
            return {"min_bytes_guard_status": "upstream_not_sealed"}
    if "validation_data" in input_dict:
        if not input_dict.get("validation_data"):
            # HARD GATE: Validation data missing or empty
            return {"min_bytes_guard_status": "validation_failed"}
    return {"min_bytes_guard_status": "ok"}
