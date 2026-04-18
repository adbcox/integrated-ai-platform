from typing import Any

def contract_pair_catalog_w5_w6(input_dict):
    if not isinstance(input_dict, dict):
        # HARD GATE: Invalid input type
        return {"contract_pair_catalog_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            # HARD GATE: Upstream seal not in sealed state
            return {"contract_pair_catalog_status": "upstream_not_sealed"}
    if "validation_data" in input_dict:
        if not input_dict.get("validation_data"):
            # HARD GATE: Validation data missing or empty
            return {"contract_pair_catalog_status": "validation_failed"}
    return {"contract_pair_catalog_status": "ok"}
