from typing import Any

def tenancy_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"tenancy_rollup_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"tenancy_rollup_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"tenancy_rollup_status": "validation_context_failed"}
    return {"tenancy_rollup_status": "ok"}
