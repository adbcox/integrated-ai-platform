from typing import Any

def b14_promotion_authority(input_dict):
    if not isinstance(input_dict, dict):
        return {"promotion_authority_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"{status_key}": "upstream_not_sealed"}
    return {"promotion_authority_status": "ok"}
