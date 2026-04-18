from typing import Any

def attestation_composer(input_dict):
    if not isinstance(input_dict, dict):
        # HARD GATE: Invalid input type
        return {"attestation_composer_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            # HARD GATE: Upstream seal not in sealed state
            return {"attestation_composer_status": "upstream_not_sealed"}
    if "validation_data" in input_dict:
        if not input_dict.get("validation_data"):
            # HARD GATE: Validation data missing or empty
            return {"attestation_composer_status": "validation_failed"}
    return {"attestation_composer_status": "ok"}
