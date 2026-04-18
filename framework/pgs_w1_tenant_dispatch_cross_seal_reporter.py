from typing import Any

def tenant_dispatch_cross_seal_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"tenant_reporter_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"tenant_reporter_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"tenant_reporter_status": "validation_context_failed"}
    return {"tenant_reporter_status": "ok"}
