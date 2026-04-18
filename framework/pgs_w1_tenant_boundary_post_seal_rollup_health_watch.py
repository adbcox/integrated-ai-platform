from typing import Any

def tenant_boundary_post_seal_rollup_health_watch(input_dict):
    if not isinstance(input_dict, dict):
        return {"tenant_health_watch_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"tenant_health_watch_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"tenant_health_watch_status": "validation_context_failed"}
    return {"tenant_health_watch_status": "ok"}
