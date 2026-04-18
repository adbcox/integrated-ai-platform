from typing import Any

def attest_ort_w3_runtime(input_dict):
    if not isinstance(input_dict, dict):
        return {"attest_ort_status": "invalid_input"}
    if "upstream_seal" in input_dict:
        if input_dict.get("upstream_seal") != "sealed":
            return {"attest_ort_status": "upstream_not_sealed"}
    if "validation_context" in input_dict:
        if not input_dict.get("validation_context"):
            return {"attest_ort_status": "validation_context_failed"}
    return {"attest_ort_status": "ok"}
