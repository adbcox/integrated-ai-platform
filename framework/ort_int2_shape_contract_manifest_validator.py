from typing import Any

def shape_contract_manifest_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"shape_contract_manifest_validator_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"shape_contract_manifest_validator_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"shape_contract_manifest_validator_status": "validation_context_failed"}
    return {"shape_contract_manifest_validator_status": "ok"}
