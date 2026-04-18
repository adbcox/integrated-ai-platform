from typing import Any

def degradation_validator_missing_int2(input_dict):
    if not isinstance(input_dict, dict):
        # HARD GATE: Invalid input type
        return {"degradation_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            # HARD GATE: Upstream seal not in sealed state
            return {"degradation_status": "upstream_not_sealed"}
    if "validation_data" in input_dict:
        if not input_dict.get("validation_data"):
            # HARD GATE: Validation data missing or empty
            return {"degradation_status": "validation_failed"}
    return {"degradation_status": "ok"}
