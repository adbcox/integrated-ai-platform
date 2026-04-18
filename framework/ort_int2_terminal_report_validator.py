from typing import Any

def terminal_report_validator(input_dict):
    if not isinstance(input_dict, dict):
        return {"terminal_report_validator_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"terminal_report_validator_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"terminal_report_validator_status": "validation_context_failed"}
    return {"terminal_report_validator_status": "ok"}
