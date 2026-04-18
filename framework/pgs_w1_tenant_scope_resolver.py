from typing import Any

def tenant_scope_resolver(input_dict):
    if not isinstance(input_dict, dict):
        return {"tenant_scope_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"tenant_scope_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"tenant_scope_status": "validation_context_failed"}
    return {"tenant_scope_status": "ok"}
