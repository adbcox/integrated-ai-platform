from typing import Any

def shape_contract_catalog(input_dict):
    if not isinstance(input_dict, dict):
        # HARD GATE: Invalid input type
        return {"shape_contract_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            # HARD GATE: Upstream seal not in sealed state
            return {"shape_contract_status": "upstream_not_sealed"}
    if "validation_data" in input_dict:
        if not input_dict.get("validation_data"):
            # HARD GATE: Validation data missing or empty
            return {"shape_contract_status": "validation_failed"}
    return {"shape_contract_status": "ok"}
