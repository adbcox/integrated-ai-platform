from typing import Any

def b2_change_normalizer(input_dict):
    if not isinstance(input_dict, dict):
        return {"change_normalizer_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"{status_key}": "upstream_not_sealed"}
    return {"change_normalizer_status": "ok"}
