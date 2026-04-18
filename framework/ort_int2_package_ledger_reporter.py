from typing import Any

def package_ledger_reporter(input_dict):
    if not isinstance(input_dict, dict):
        return {"package_ledger_reporter_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"package_ledger_reporter_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"package_ledger_reporter_status": "validation_context_failed"}
    return {"package_ledger_reporter_status": "ok"}
