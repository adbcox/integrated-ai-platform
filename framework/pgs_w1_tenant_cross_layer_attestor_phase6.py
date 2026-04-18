from typing import Any

def tenant_cross_layer_attestor_phase6(input_dict):
    if not isinstance(input_dict, dict):
        return {"tenant_cross_layer_attestor_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"tenant_cross_layer_attestor_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"tenant_cross_layer_attestor_status": "validation_context_failed"}
    return {"tenant_cross_layer_attestor_status": "ok"}
