from typing import Any

def b4_change_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"change_validator_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"{status_key}": "upstream_not_sealed"}
    return {"change_validator_status": "ok"}
