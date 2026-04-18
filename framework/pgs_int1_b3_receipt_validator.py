from typing import Any

def b3_receipt_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"pgs_int1_b3_receipt_validator_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"{status_key}": "upstream_not_sealed"}
    return {"pgs_int1_b3_receipt_validator_status": "ok"}
