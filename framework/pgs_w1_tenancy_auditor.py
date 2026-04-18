from typing import Any

def tenancy_auditor(input_dict):
    if not isinstance(input_dict, dict):
        return {"tenancy_auditor_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"tenancy_auditor_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"tenancy_auditor_status": "validation_context_failed"}
    return {"tenancy_auditor_status": "ok"}
