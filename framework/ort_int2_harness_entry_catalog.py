from typing import Any

def harness_entry_catalog(input_dict):
    if not isinstance(input_dict, dict):
        return {"harness_entry_catalog_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"harness_entry_catalog_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"harness_entry_catalog_status": "validation_context_failed"}
    return {"harness_entry_catalog_status": "ok"}
