from typing import Any

def cross_tenant_non_interference_post_seal_rollup(input_dict):
    if not isinstance(input_dict, dict):
        return {"cross_tenant_non_interference_post_seal_rollup_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"cross_tenant_non_interference_post_seal_rollup_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"cross_tenant_non_interference_post_seal_rollup_status": "validation_context_failed"}
    return {"cross_tenant_non_interference_post_seal_rollup_status": "ok"}
