from typing import Any

def shape_contract_manifest_w1_w2(input_dict):
    if not isinstance(input_dict, dict):
        return {"shape_contract_manifest_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"shape_contract_manifest_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"shape_contract_manifest_status": "validation_context_failed"}
    return {"shape_contract_manifest_status": "ok"}
