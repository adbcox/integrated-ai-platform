from typing import Any

def attest_lob_int3(input_dict):
    if not isinstance(input_dict, dict):
        return {"attest_lob_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"attest_lob_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"attest_lob_status": "validation_context_failed"}
    return {"attest_lob_status": "ok"}
